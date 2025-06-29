import asyncio
import json
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, quote

from loguru import logger
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


class WebSearchTool:
    """
    A tool to perform web searches using Crawl4AI to scrape DuckDuckGo.
    It extracts search results including title, URL, and snippet.
    """

    def __init__(self):
        self.name = "web_search"
        self.search_engine_url = "https://html.duckduckgo.com/html/"

        # Schema to extract search results from DuckDuckGo's HTML version.
        # The output JSON will have a top-level key 'results'
        # containing a list of the extracted items.
        schema = {
            "name": "Search Results",
            "baseSelector": "div.result",
            "collection_name": "results",
            "fields": [
                {"name": "title", "selector": "h2.result__title > a.result__a", "type": "text"},
                {"name": "url", "selector": "h2.result__title > a.result__a", "type": "attribute", "attribute": "href"},
                {"name": "snippet", "selector": "a.result__snippet", "type": "text"}
            ]
        }
        self.extraction_strategy = JsonCssExtractionStrategy(schema)

    async def _arun(self, query: str) -> List[Dict[str, Any]]:
        """
        Performs a web search on DuckDuckGo and returns structured results.

        Args:
            query: The search query string.

        Returns:
            A list of dictionaries, where each dictionary represents a search result
            with 'title', 'url', and 'snippet'.
        """
        search_url = f"{self.search_engine_url}?q={quote(query)}"
        logger.info(f"Performing web search for: '{query}'")
        logger.debug(f"Searching at URL: {search_url}")

        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,  # Ensure fresh results for every search
            extraction_strategy=self.extraction_strategy
        )

        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=search_url, config=config)

                if not result or not result.extracted_content:
                    logger.warning(f"No content extracted for query: '{query}'")
                    return []

                # The result from JsonCssExtractionStrategy is a JSON string
                data = json.loads(result.extracted_content)

                # The schema defines 'results' as the collection name
                search_results = data.get("results", [])
                if not search_results:
                    logger.info(f"No search results found for query: '{query}'")
                    return []

                cleaned_results = []
                for item in search_results:
                    if not isinstance(item, dict):
                        continue
                        
                    raw_url = item.get("url")
                    if not raw_url:
                        continue

                    try:
                        parsed_url = urlparse(raw_url)
                        query_params = parse_qs(parsed_url.query)
                        real_url = query_params.get("uddg", [None])[0]

                        if real_url:
                            cleaned_results.append({
                                "title": (item.get("title") or "").strip(),
                                "url": real_url,
                                "snippet": (item.get("snippet") or "").strip().replace("\n", " ")
                            })
                    except Exception as e:
                        logger.warning(f"Could not parse URL from DDG result: {raw_url}. Error: {e}")
                        continue

                logger.success(f"Found {len(cleaned_results)} results for query: '{query}'")
                return cleaned_results

        except Exception as e:
            logger.error(f"An error occurred during web search for query '{query}': {e}")
            return []