import asyncio
import chromadb
import logging
from typing import List, Dict, Any, Optional, Tuple
from src.config import Config
from cachetools import TTLCache
from functools import partial

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, storage_path: str = Config.RAG_STORAGE_PATH):
        self.storage_path = storage_path
        self.client: Optional[chromadb.PersistentClient] = None
        self.collection: Optional[chromadb.Collection] = None
        self.cache = TTLCache(maxsize=1000, ttl=3600)  # Cache with 1000 items and 1 hour TTL

    async def initialize(self):
        logger.info("Initializing RAG service...")
        try:
            self.client = chromadb.PersistentClient(path=self.storage_path)
            self.collection = self.client.get_or_create_collection(
                name=Config.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"} 
            )
            logger.info(f"RAG service initialized with storage path: {self.storage_path}")
        except Exception as e:
            logger.exception("Failed to initialize RAG service")
            raise RuntimeError(f"Failed to initialize RAG service: {str(e)}")

    async def cleanup(self):
        logger.info("Cleaning up RAG service...")
        self.client = None
        self.collection = None
        self.cache.clear()
        logger.info("RAG service cleaned up")

    async def _ensure_initialized(self):
        if not self.client or not self.collection:
            await self.initialize()

    async def store_document(self, text: str, doc_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        await self._ensure_initialized()
        try:
            await asyncio.to_thread(self.collection.add, documents=[text], ids=[doc_id], metadatas=[metadata] if metadata else None)
            self.cache[doc_id] = {"text": text, "metadata": metadata}
            logger.info(f"Document stored successfully: {doc_id}")
            return True
        except Exception as e:
            logger.exception(f"Error storing document in RAG: {doc_id}")
            raise RuntimeError(f"Error storing document in RAG: {str(e)}")

    async def retrieve_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        await self._ensure_initialized()
        try:
            if doc_id in self.cache:
                logger.info(f"Document retrieved from cache: {doc_id}")
                return self.cache[doc_id]

            results = await asyncio.to_thread(self.collection.get, ids=[doc_id])
            if results["documents"]:
                doc = {"text": results["documents"][0], "metadata": results["metadatas"][0] if results["metadatas"] else None}
                self.cache[doc_id] = doc
                logger.info(f"Document retrieved successfully: {doc_id}")
                return doc
            logger.warning(f"Document not found: {doc_id}")
            return None
        except Exception as e:
            logger.exception(f"Error retrieving document from RAG: {doc_id}")
            raise RuntimeError(f"Error retrieving document from RAG: {str(e)}")

    async def search_documents(self, query: str, n_results: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        await self._ensure_initialized()
        try:
            results = await asyncio.to_thread(
                self.collection.query, 
                query_texts=[query], 
                n_results=n_results,
                where=filter
            )
            logger.info(f"Search completed for query: {query}")
            return [{"id": id, "text": doc, "metadata": meta} for id, doc, meta in zip(results["ids"][0], results["documents"][0], results["metadatas"][0])]
        except Exception as e:
            logger.exception(f"Error searching documents: {query}")
            raise RuntimeError(f"Error searching documents: {str(e)}")

    async def delete_document(self, doc_id: str) -> bool:
        await self._ensure_initialized()
        try:
            await asyncio.to_thread(self.collection.delete, ids=[doc_id])
            if doc_id in self.cache:
                del self.cache[doc_id]
            logger.info(f"Document deleted successfully: {doc_id}")
            return True
        except Exception as e:
            logger.exception(f"Error deleting document: {doc_id}")
            raise RuntimeError(f"Error deleting document: {str(e)}")

    async def batch_store_documents(self, texts: List[str], doc_ids: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> bool:
        await self._ensure_initialized()
        try:
            batch_size = 1000  # Adjust this based on your system's capabilities
            for i in range(0, len(doc_ids), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_ids = doc_ids[i:i+batch_size]
                batch_metadatas = metadatas[i:i+batch_size] if metadatas else None
                await asyncio.to_thread(self.collection.add, documents=batch_texts, ids=batch_ids, metadatas=batch_metadatas)
                for id, text, meta in zip(batch_ids, batch_texts, batch_metadatas or [None]*len(batch_ids)):
                    self.cache[id] = {"text": text, "metadata": meta}
            logger.info(f"Batch storage successful for {len(doc_ids)} documents")
            return True
        except Exception as e:
            logger.exception("Error in batch storing documents")
            raise RuntimeError(f"Error in batch storing documents: {str(e)}")

    async def batch_retrieve_documents(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        await self._ensure_initialized()
        try:
            cached_docs = [self.cache.get(id) for id in doc_ids]
            missing_ids = [id for id, doc in zip(doc_ids, cached_docs) if doc is None]
            
            if missing_ids:
                results = await asyncio.to_thread(self.collection.get, ids=missing_ids)
                for id, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
                    self.cache[id] = {"text": doc, "metadata": meta}
            
            documents = [self.cache[id] for id in doc_ids]
            logger.info(f"Batch retrieval successful for {len(doc_ids)} documents")
            return [{"id": id, **doc} for id, doc in zip(doc_ids, documents)]
        except Exception as e:
            logger.exception("Error in batch retrieving documents")
            raise RuntimeError(f"Error in batch retrieving documents: {str(e)}")

    async def clear_all_documents(self) -> bool:
        await self._ensure_initialized()
        try:
            all_ids = await asyncio.to_thread(lambda: self.collection.get()["ids"])
            if all_ids:
                await asyncio.to_thread(self.collection.delete, ids=all_ids)
                logger.info(f"All documents ({len(all_ids)}) cleared from the RAG system")
            else:
                logger.info("No documents to clear from the RAG system")
            return True
        except Exception as e:
            logger.exception("Error clearing all documents")
            raise RuntimeError(f"Error clearing all documents: {str(e)}")

    async def update_document(self, doc_id: str, new_text: str, new_metadata: Optional[Dict[str, Any]] = None) -> bool:
        await self._ensure_initialized()
        try:
            await asyncio.to_thread(self.collection.update, ids=[doc_id], documents=[new_text], metadatas=[new_metadata] if new_metadata else None)
            logger.info(f"Document updated successfully: {doc_id}")
            return True
        except Exception as e:
            logger.exception(f"Error updating document: {doc_id}")
            raise RuntimeError(f"Error updating document: {str(e)}")

    async def get_collection_stats(self) -> Dict[str, Any]:
        await self._ensure_initialized()
        try:
            stats = await asyncio.to_thread(self.collection.count)
            logger.info(f"Retrieved collection stats: {stats} documents")
            return {"document_count": stats}
        except Exception as e:
            logger.exception("Error getting collection stats")
            raise RuntimeError(f"Error getting collection stats: {str(e)}")