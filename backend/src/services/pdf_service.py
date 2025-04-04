import logging
import os
import fitz
import asyncio
import re
import unicodedata
from typing import Dict, Any, Optional, List, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from src.config import Config
from cachetools import TTLCache
import threading

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)  # Adjust the number of workers as needed
        self.cache = TTLCache(maxsize=1000, ttl=3600)
        self.cache_lock = threading.Lock()

    async def initialize(self):
        logger.info("Initializing PDFService...")
        logger.info("PDFService initialized successfully")

    async def cleanup(self):
        logger.info("Cleaning up PDFService...")
        self.executor.shutdown()
        logger.info("PDFService cleaned up")

    @staticmethod
    def extract_text_from_page(page: fitz.Page) -> str:
        text = page.get_text()
        return PDFService.clean_text(text)

    @staticmethod
    def clean_text(text: str) -> str:
        text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def check_pdf(file_path: str) -> bool:
        try:
            with fitz.open(file_path) as doc:
                return doc.is_pdf and len(doc) > 0
        except Exception as e:
            logger.error(f"Error opening PDF: {file_path}. Error: {str(e)}")
            return False

    def extract_text(self, pdf_path: str, start_page: int = 0, end_page: Optional[int] = None) -> str:
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            end = end_page if end_page is not None else total_pages
            text_list = [self.extract_text_from_page(doc[i]) for i in range(start_page, end)]
            return "\n".join(text_list)

    def cached_extract_text(self, pdf_path: str, start_page: int = 0, end_page: Optional[int] = None) -> str:
        cache_key = f"{pdf_path}:{start_page}:{end_page}"
        with self.cache_lock:
            if cache_key in self.cache:
                return self.cache[cache_key]
        
        text = self.extract_text(pdf_path, start_page, end_page)
        
        with self.cache_lock:
            self.cache[cache_key] = text
        
        return text

    async def extract_text_from_pdf(self, pdf_path: str, start_page: int = 0, end_page: Optional[int] = None) -> str:
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            logger.info(f"Starting text extraction from PDF: {pdf_path}")
            
            text = await asyncio.get_running_loop().run_in_executor(
                self.executor, self.cached_extract_text, pdf_path, start_page, end_page
            )

            if not text:
                logger.warning(f"No text extracted from PDF: {pdf_path}")
                raise ValueError("No text extracted from PDF")

            logger.info(f"Successfully extracted and cleaned text from PDF: {pdf_path}")
            return text
        except fitz.FileDataError as e:
            logger.error(f"Invalid or corrupted PDF file: {pdf_path}")
            raise ValueError(f"Invalid or corrupted PDF file: {str(e)}")
        except Exception as e:
            logger.exception(f"Error extracting text from PDF: {pdf_path}")
            raise RuntimeError(f"Error extracting text from PDF: {str(e)}")

        
    async def is_valid_pdf(self, file_path: str) -> bool:
        """Checks if the given file is a valid PDF."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        try:
            is_valid = await asyncio.get_running_loop().run_in_executor(self.executor, self.check_pdf, file_path)
            if is_valid:
                logger.info(f"Valid PDF file: {file_path}")
            else:
                logger.warning(f"Invalid PDF file: {file_path}")
            return is_valid
        except Exception as e:
            logger.exception(f"Unexpected error checking PDF validity: {file_path}. Error: {str(e)}")
            return False

    


    @staticmethod
    def extract_metadata(pdf_path: str) -> Dict[str, Any]:
        with fitz.open(pdf_path) as doc:
            return dict(doc.metadata)

    async def extract_pdf_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts metadata from a PDF file."""
        try:
            metadata = await asyncio.get_running_loop().run_in_executor(self.executor, self.extract_metadata, pdf_path)
            logger.info(f"Successfully extracted metadata from PDF: {pdf_path}")
            return metadata
        except Exception as e:
            logger.exception(f"Error extracting metadata from PDF: {pdf_path}")
            raise RuntimeError(f"Error extracting metadata from PDF: {str(e)}")

    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        with fitz.open(pdf_path) as doc:
            return len(doc)

    async def get_pdf_page_count(self, pdf_path: str) -> int:
        """Gets the number of pages in a PDF file."""
        try:
            page_count = await asyncio.get_running_loop().run_in_executor(self.executor, self.get_page_count, pdf_path)
            logger.info(f"Successfully got page count for PDF: {pdf_path}")
            return page_count
        except Exception as e:
            logger.exception(f"Error getting page count for PDF: {pdf_path}")
            raise RuntimeError(f"Error getting page count for PDF: {str(e)}")

    async def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Processes a PDF file, extracting text, metadata, and page count."""
        try:
            text_task = self.extract_text_from_pdf(pdf_path)
            metadata_task = self.extract_pdf_metadata(pdf_path)
            page_count_task = self.get_pdf_page_count(pdf_path)

            text, metadata, page_count = await asyncio.gather(text_task, metadata_task, page_count_task)

            return {
                "text": text,
                "metadata": metadata,
                "page_count": page_count
            }
        except Exception as e:
            logger.exception(f"Error processing PDF: {pdf_path}")
            raise RuntimeError(f"Error processing PDF: {str(e)}")

    @staticmethod
    async def extract_chunks_generator(pdf_path: str, chunk_size: int = 1000) -> AsyncGenerator[str, None]:
        with fitz.open(pdf_path) as doc:
            text = ""
            for page in doc:
                page_text = PDFService.extract_text_from_page(page)
                text += page_text
                while len(text) >= chunk_size:
                    chunk, text = text[:chunk_size], text[chunk_size:]
                    yield chunk
            if text:
                yield text

    async def extract_text_chunks(self, pdf_path: str, chunk_size: int = 1000) -> List[str]:
        """Extracts text from PDF in chunks."""
        try:
            chunks = []
            async for chunk in self.extract_chunks_generator(pdf_path, chunk_size):
                chunks.append(chunk)
            logger.info(f"Successfully extracted {len(chunks)} chunks from PDF: {pdf_path}")
            return chunks
        except Exception as e:
            logger.exception(f"Error extracting text chunks from PDF: {pdf_path}")
            raise RuntimeError(f"Error extracting text chunks from PDF: {str(e)}")