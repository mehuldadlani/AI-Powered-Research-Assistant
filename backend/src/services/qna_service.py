import os
import tempfile
from typing import List, Tuple, Dict, Any, Optional
import asyncio
import chromadb
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import CrossEncoder
from src.config import Config
from src.services.rag_service import RAGService
from src.services.crew_service import CrewAIService
from cachetools import TTLCache

import logging

logger = logging.getLogger(__name__)

class QnAService:
    def __init__(self, rag_service: RAGService, crew_service: CrewAIService):
        self.rag_service = rag_service
        self.crew_service = crew_service
        self.ollama_ef = OllamaEmbeddingFunction(
            url=Config.OLLAMA_API_URL,
            model_name=Config.OLLAMA_EMBEDDING_MODEL,
        )
        self.chroma_client = chromadb.PersistentClient(path=Config.CHROMA_DB_PATH)
        self.collection = self.chroma_client.get_or_create_collection(
            name=Config.CHROMA_COLLECTION_NAME,
            embedding_function=self.ollama_ef,
            metadata={"hnsw:space": "cosine"},
        )
        self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.cache = TTLCache(maxsize=1000, ttl=3600)  # Cache with 1000 items and 1 hour TTL

    async def initialize(self):
        logger.info("Initializing QnAService...")
        # Add any initialization logic if needed
        logger.info("QnAService initialized successfully")

    async def cleanup(self):
        logger.info("Cleaning up QnAService...")
        self.cache.clear()
        logger.info("QnAService cleaned up")

    async def store_document(self, text: str, doc_id: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, bool, Dict[str, Any]]:
        await self._ensure_initialized()
        try:
            content_hash = self.compute_content_hash(text)
            
            # Check if a document with the same content hash already exists
            existing_doc = await self.get_document_by_content_hash(content_hash)

            if existing_doc:
                logger.info(f"Document with same content already exists: {existing_doc['id']}")
                return existing_doc['id'], False, existing_doc

            if metadata is None:
                metadata = {}
            metadata['content_hash'] = content_hash
            metadata['original_filename'] = doc_id

            await asyncio.to_thread(self.collection.add, documents=[text], ids=[doc_id], metadatas=[metadata])
            doc_info = {"id": doc_id, "text": text, "metadata": metadata, "content_hash": content_hash}
            self.cache[doc_id] = doc_info
            
            logger.info(f"Document stored: {doc_id}")
            
            return doc_id, True, doc_info

        except Exception as e:
            logger.exception(f"Error storing document in RAG: {doc_id}")
            raise RuntimeError(f"Error storing document in RAG: {str(e)}")

    async def add_to_vector_collection(self, splits: List[Document], file_name: str):
        try:
            documents, metadatas, ids = [], [], []
            for idx, split in enumerate(splits):
                documents.append(split.page_content)
                metadatas.append(split.metadata)
                ids.append(f"{file_name}_{idx}")

            # Process in batches of 1000
            batch_size = 1000
            for i in range(0, len(ids), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                batch_metadatas = metadatas[i:i+batch_size]
                await self.rag_service.batch_store_documents(batch_docs, batch_ids, batch_metadatas)

            logger.info(f"Added {len(splits)} document chunks to RAG for file: {file_name}")
        except Exception as e:
            logger.error(f"Error adding document chunks to RAG for file {file_name}: {str(e)}")
            raise

    async def query_collection(self, prompt: str, n_results: int = 10) -> List[str]:
        cache_key = f"query_{prompt}_{n_results}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            results = await self.rag_service.search_documents(prompt, n_results)
            if isinstance(results, dict) and 'documents' in results:
                documents = results['documents']
            elif isinstance(results, list):
                documents = results
            else:
                logger.error(f"Unexpected results format from RAG service: {type(results)}")
                raise ValueError("Unexpected results format from RAG service")
            
            self.cache[cache_key] = documents
            return documents
        except Exception as e:
            logger.error(f"Error querying collection: {str(e)}")
            raise

    async def call_llm(self, context: str, prompt: str) -> str:
        system_prompt = """
        You are an AI assistant tasked with providing detailed answers based solely on the given context. Your goal is to analyze the information provided and formulate a comprehensive, well-structured response to the question.

        To answer the question:
        1. Thoroughly analyze the context, identifying key information relevant to the question.
        2. Organize your thoughts and plan your response to ensure a logical flow of information.
        3. Formulate a detailed answer that directly addresses the question, using only the information provided in the context.
        4. Ensure your answer is comprehensive, covering all relevant aspects found in the context.
        5. If the context doesn't contain sufficient information to fully answer the question, state this clearly in your response.

        Format your response as follows:
        1. Use clear, concise language.
        2. Organize your answer into paragraphs for readability.
        3. Use bullet points or numbered lists where appropriate to break down complex information.
        4. If relevant, include any headings or subheadings to structure your response.
        5. Ensure proper grammar, punctuation, and spelling throughout your answer.

        Important: Base your entire response solely on the information provided in the context. Do not include any external knowledge or assumptions not present in the given text.
        """
        
        full_prompt = f"Context: {context}\nQuestion: {prompt}"
        try:
            crew_result = await self.crew_service.analyze_with_crew(system_prompt, full_prompt)
            
            if isinstance(crew_result, dict) and 'result' in crew_result:
                return crew_result['result']
            else:
                logger.warning(f"Unexpected CrewOutput structure: {crew_result}")
                return str(crew_result)
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            raise

    async def re_rank_cross_encoders(self, documents: List[Any], prompt: str) -> Tuple[str, List[int]]:
        try:
            # Ensure documents are strings
            str_documents = [str(doc) if not isinstance(doc, str) else doc for doc in documents]
            
            ranks = await asyncio.to_thread(self.cross_encoder.rank, prompt, str_documents, top_k=3)
            relevant_text = ""
            relevant_text_ids = []
            for rank in ranks:
                relevant_text += str_documents[rank["corpus_id"]] + "\n\n"  # Add some separation between documents
                relevant_text_ids.append(rank["corpus_id"])
            return relevant_text.strip(), relevant_text_ids
        except Exception as e:
            logger.error(f"Error re-ranking with cross encoders: {str(e)}")
            raise

    async def answer_question(self, prompt: str, doc_id: Optional[str] = None) -> Dict[str, Any]:
        cache_key = f"answer_{prompt}_{doc_id}"
        if cache_key in self.cache:
            logger.info(f"Returning cached answer for prompt: {prompt}")
            return self.cache[cache_key]

        try:
            logger.info(f"Answering question. Prompt: '{prompt}', Doc ID: '{doc_id}'")
            
            if doc_id:
                logger.info(f"Retrieving specific document: {doc_id}")
                doc = await self.rag_service.retrieve_document(doc_id)
                if doc is None or 'text' not in doc or not doc['text']:
                    logger.warning(f"Document not found or has no content: {doc_id}")
                    return {"answer": f"I'm sorry, but I couldn't find any document with the ID {doc_id} or it has no content."}
                
                context = [doc['text']]
                logger.info(f"Retrieved document. Content length: {len(context[0])}")
            else:
                logger.info("Querying collection for relevant documents")
                context = await self.query_collection(prompt)
                logger.info(f"Query results received: {len(context)} documents")
            
            if not context:
                logger.warning("No relevant documents found")
                return {"answer": "I'm sorry, but I couldn't find any relevant information to answer your question."}
        
            logger.info("Re-ranking documents with cross-encoder")
            relevant_text, relevant_text_ids = await self.re_rank_cross_encoders(context, prompt)
            logger.info(f"Re-ranking complete. Relevant text length: {len(relevant_text)}")
            
            if not relevant_text:
                logger.warning("No relevant text after re-ranking")
                return {"answer": "I'm sorry, but I couldn't find any relevant information to answer your question."}
            
            logger.info("Calling LLM for response")
            response = await self.call_llm(context=relevant_text, prompt=prompt)
            logger.info("LLM response received")
            
            result = {
                "answer": response,
                "relevant_text_ids": relevant_text_ids,
                "relevant_text": relevant_text,
                "full_results": context
            }
            self.cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}", exc_info=True)
            return {"error": f"An error occurred while processing your question: {str(e)}"}
        
    async def document_exists(self, doc_id: str) -> bool:
        try:
            logger.info(f"Checking existence of document: {doc_id}")
            doc = await self.rag_service.retrieve_document(doc_id)
            exists = doc is not None and 'text' in doc and doc['text'] is not None
            logger.info(f"Document {doc_id} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"Error checking document existence: {str(e)}")
            return False