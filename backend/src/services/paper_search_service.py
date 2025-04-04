import asyncio
import aiohttp
from bs4 import BeautifulSoup
from scholarly import scholarly
import logging
from typing import List, Dict, Any, Optional
from src.config import Config
from src.services.rag_service import RAGService
from src.services.crew_service import CrewAIService

logger = logging.getLogger(__name__)

class PaperSearchService:
    def __init__(self, rag_service: RAGService, crew_service: CrewAIService):
        self.rag_service = rag_service
        self.crew_service = crew_service

    async def initialize(self):
        logger.info("Initializing PaperSearchService...")
        # Add any initialization logic if needed
        logger.info("PaperSearchService initialized successfully")

    async def cleanup(self):
        logger.info("Cleaning up PaperSearchService...")
        # Add any cleanup logic if needed
        logger.info("PaperSearchService cleaned up")

    async def fetch_google_scholar(self, query: str) -> List[str]:
        try:
            results = []
            search_query = scholarly.search_pubs(query)
            for paper in search_query:
                results.append(paper['bib']['title'])
                if len(results) >= Config.GOOGLE_SCHOLAR_MAX_RESULTS:
                    break
            logger.info(f"Fetched {len(results)} results from Google Scholar")
            return results
        except Exception as e:
            logger.error(f"Error fetching from Google Scholar: {str(e)}")
            return []

    async def fetch_arxiv(self, query: str) -> List[str]:
        base_url = "http://export.arxiv.org/api/query?"
        search_query = f"search_query=all:{query}&start=0&max_results={Config.ARXIV_MAX_RESULTS}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url + search_query) as response:
                    soup = BeautifulSoup(await response.text(), 'xml')
                    results = [entry.title.text for entry in soup.find_all('entry')]
            logger.info(f"Fetched {len(results)} results from ArXiv")
            return results
        except Exception as e:
            logger.error(f"Error fetching from ArXiv: {str(e)}")
            return []

    async def fetch_author_details(self, author_name: str) -> Optional[Dict[str, Any]]:
        try:
            author = next(scholarly.search_author(author_name), None)
            if not author:
                logger.warning(f"Author not found: {author_name}")
                return None
            scholarly.fill(author)
            top_cited = sorted(author['publications'], key=lambda x: x.get('num_citations', 0), reverse=True)[:Config.AUTHOR_TOP_CITED_COUNT]
            recent_papers = sorted(author['publications'], key=lambda x: x['bib'].get('year', 0), reverse=True)[:Config.AUTHOR_RECENT_PAPERS_COUNT]
            author_details = {
                "name": author['name'],
                "affiliation": author.get('affiliation', 'Unknown'),
                "top_cited": [paper['bib']['title'] for paper in top_cited],
                "recent_papers": [paper['bib']['title'] for paper in recent_papers],
            }
            logger.info(f"Fetched details for author: {author_name}")
            return author_details
        except Exception as e:
            logger.error(f"Error fetching author details: {str(e)}")
            return None

    async def search_papers(self, query: str) -> List[str]:
        scholar_results = await self.fetch_google_scholar(query)
        arxiv_results = await self.fetch_arxiv(query)
        all_results = scholar_results + arxiv_results
        
        # Store results in RAG
        tasks = [self.rag_service.store_document(paper, f"search_result_{query}_{i}") 
                 for i, paper in enumerate(all_results)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error storing search result {i} in RAG: {str(result)}")
        
        logger.info(f"Completed paper search for query: {query}")
        return all_results

    async def search_author(self, author_name: str) -> Optional[Dict[str, Any]]:
        author_details = await self.fetch_author_details(author_name)
        if author_details:
            try:
                await self.rag_service.store_document(str(author_details), f"author_{author_name}")
                logger.info(f"Stored author details in RAG for: {author_name}")
            except Exception as e:
                logger.error(f"Error storing author details in RAG: {str(e)}")
        return author_details
    
    async def analyze_search_results(self, query: str, results: List[str]) -> Optional[str]:
        analysis_prompt = f"""
        Analyze the following search results for the query "{query}":
        
        {results}
        
        Provide a summary of the main themes, identify any notable trends or patterns,
        and suggest potential areas for further research based on these results.
        """
        
        try:
            analysis = await self.crew_service.analyze_with_crew("Analyze search results", analysis_prompt)
            logger.info(f"Completed analysis of search results for query: {query}")
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing search results: {str(e)}")
            return None

    async def enhanced_paper_search(self, query: str) -> Dict[str, Any]:
        search_results = await self.search_papers(query)
        analysis = await self.analyze_search_results(query, search_results)
        
        return {
            "search_results": search_results,
            "analysis": analysis
        }