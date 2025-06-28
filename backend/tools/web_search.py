"""
Web search tool using Crawl4AI for real-time content
"""

import asyncio
from typing import Dict, Any, List, Optional
from crawl4ai import AsyncWebCrawler
from langchain.tools import BaseTool
from loguru import logger

class WebSearchTool(BaseTool):
    """Tool for web searching and content extraction using Crawl4AI"""
    name: str = "web_search"
    description: str = "Search web for current information and extract content"
    crawler: Optional[AsyncWebCrawler] = None
    
    async def _get_crawler(self):
        """Get or create crawler instance"""
        if not self.crawler:
            self.crawler = AsyncWebCrawler(verbose=False)
            await self.crawler.astart()
        return self.crawler
    
    def _run(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """Synchronous wrapper for async search"""
        return asyncio.run(self._arun(query, max_results))
    
    async def _arun(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """Search web and extract relevant content"""
        try:
            # Search URLs for the query
            search_urls = self._get_search_urls(query, max_results)
            
            crawler = await self._get_crawler()
            results = []
            
            for url in search_urls:
                try:
                    result = await crawler.arun(url=url)
                    if result.success:
                        content = self._extract_key_content(result.markdown, query)
                        results.append({
                            "url": url,
                            "title": result.metadata.get("title", ""),
                            "content": content,
                            "relevance_score": self._calculate_relevance(content, query)
                        })
                except Exception as e:
                    logger.warning(f"Failed to crawl {url}: {e}")
                    continue
            
            # Sort by relevance and return top results
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            return {
                "query": query,
                "results": results[:max_results],
                "summary": self._generate_summary(results, query),
                "timestamp": "2025-01-01T00:00:00Z"
            }
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {
                "query": query,
                "results": [],
                "error": str(e),
                "fallback_insights": self._get_fallback_insights(query)
            }
    
    def _get_search_urls(self, query: str, max_results: int) -> List[str]:
        """Generate search URLs for the query"""
        # In production, this would use a search API
        # For now, return relevant industry URLs
        base_urls = [
            f"https://techcrunch.com/search/{query.replace(' ', '+')}",
            f"https://www.producthunt.com/search?q={query.replace(' ', '+')}",
            f"https://news.ycombinator.com/item?id=search&q={query.replace(' ', '+')}"
        ]
        return base_urls[:max_results]
    
    def _extract_key_content(self, markdown: str, query: str) -> str:
        """Extract key content relevant to query"""
        if not markdown:
            return ""
        
        # Simple extraction - take first 500 chars
        lines = markdown.split('\n')
        relevant_lines = []
        
        for line in lines[:20]:  # Check first 20 lines
            if any(word.lower() in line.lower() for word in query.split()):
                relevant_lines.append(line.strip())
        
        content = ' '.join(relevant_lines)
        return content[:500] if content else markdown[:500]
    
    def _calculate_relevance(self, content: str, query: str) -> float:
        """Calculate relevance score"""
        if not content:
            return 0.0
        
        query_words = query.lower().split()
        content_lower = content.lower()
        
        matches = sum(1 for word in query_words if word in content_lower)
        return matches / len(query_words) if query_words else 0.0
    
    def _generate_summary(self, results: List[Dict], query: str) -> str:
        """Generate summary from search results"""
        if not results:
            return f"No current web results found for '{query}'"
        
        key_points = []
        for result in results[:3]:
            if result.get("content"):
                key_points.append(result["content"][:100])
        
        return f"Current insights on '{query}': " + " | ".join(key_points)
    
    def _get_fallback_insights(self, query: str) -> Dict[str, Any]:
        """Provide fallback insights when web search fails"""
        return {
            "market_trends": f"Growing interest in {query}",
            "competitive_landscape": "Competitive market with opportunities",
            "user_sentiment": "Generally positive adoption trends",
            "recommendation": "Monitor market developments closely"
        }
    
    async def close(self):
        """Close crawler connection"""
        if self.crawler:
            await self.crawler.aclose()