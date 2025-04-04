import logging
import asyncio
from functools import lru_cache
from typing import Dict, Any
from src.services.crew_service import CrewAIService
from src.config import Config

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, crew_service: CrewAIService):
        self.crew_service = crew_service
        self.summarization_count = 0
        self.cache_hit_count = 0

    async def initialize(self):
        logger.info("Initializing AIService...")
        # Add any initialization logic if needed
        logger.info("AIService initialized successfully")

    async def cleanup(self):
        logger.info("Cleaning up AIService...")
        # Add any cleanup logic if needed
        logger.info("AIService cleaned up")

    async def summarize_text(self, text: Any, level: str) -> str:
        """Generates a summary based on the selected expertise level using CrewAI."""
        if level not in Config.ALLOWED_LEVELS:
            logger.error(f"Invalid summarization level: {level}")
            raise ValueError(f"Invalid summarization level: {level}")

        try:
            logger.info(f"Starting summarization with level: {level}")
            start_time = asyncio.get_event_loop().time()
            
            # Convert text to string if it's not already
            if not isinstance(text, str):
                text = str(text)
            
            summary = await asyncio.wait_for(
                self.crew_service.summarize_with_crew(text, level),
                timeout=Config.SUMMARIZATION_TIMEOUT
            )
            
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            logger.info(f"Summarization completed successfully in {duration:.2f} seconds")
            
            # Ensure the summary is a string
            summary = str(summary)
            
            return summary
        except asyncio.TimeoutError:
            logger.error("Summarization timed out")
            raise TimeoutError("Summarization process timed out")
        except Exception as e:
            logger.exception(f"Error generating summary with CrewAI: {str(e)}")
            raise

    @lru_cache(maxsize=Config.SUMMARY_CACHE_SIZE)
    async def _cached_summary(self, text: str, level: str) -> str:
        return await self.summarize_text(text, level)

    async def get_or_create_summary(self, text: str, level: str) -> str:
        """Retrieves a cached summary or generates a new one."""
        if not Config.USE_SUMMARY_CACHE:
            return await self.summarize_text(text, level)

        cache_key = f"{hash(text)}:{level}"
        try:
            summary = await self._cached_summary(text, level)
            logger.info("Returning cached summary")
            self.cache_hit_count += 1
            return summary
        except Exception as e:
            logger.exception(f"Error retrieving/generating summary: {str(e)}")
            raise

    async def retry_summarize(self, text: str, level: str, max_retries: int = 3) -> str:
        """Retry summarization with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await self.get_or_create_summary(text, level)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"All retry attempts failed for summarization")
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Summarization attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

    async def summarize_with_metrics(self, text: str, level: str) -> str:
        """Summarize text and update metrics."""
        self.summarization_count += 1
        return await self.retry_summarize(text, level)

    def get_metrics(self) -> Dict[str, Any]:
        """Return current metrics."""
        return {
            "total_summarizations": self.summarization_count,
            "cache_hits": self.cache_hit_count,
            "cache_hit_rate": self.cache_hit_count / self.summarization_count if self.summarization_count > 0 else 0,
            "cache_info": self._cached_summary.cache_info() if Config.USE_SUMMARY_CACHE else None
        }