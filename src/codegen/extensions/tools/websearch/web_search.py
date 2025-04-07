"""Web search implementation."""

import os
import requests
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field

from codegen.extensions.tools.websearch.baidu_search import BaiduSearchEngine
from codegen.extensions.tools.websearch.bing_search import BingSearchEngine
from codegen.extensions.tools.websearch.duckduckgo_search import DuckDuckGoSearchEngine
from codegen.extensions.tools.websearch.google_search import GoogleSearchEngine
from codegen.extensions.tools.websearch.base import SearchItem, WebSearchEngine


class SearchMetadata(BaseModel):
    """Metadata about a search operation."""

    engine: str = Field(description="Search engine used")
    query: str = Field(description="Original search query")
    time_taken: Optional[float] = Field(default=None, description="Time taken for search in seconds")
    total_results: Optional[int] = Field(default=None, description="Total number of results found")


class SearchResult(BaseModel):
    """A single search result with additional metadata."""

    title: str = Field(description="Title of the search result")
    url: str = Field(description="URL of the search result")
    description: str = Field(description="Description or snippet of the search result")
    raw_content: Optional[str] = Field(default=None, description="Full content of the page if fetched")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the result")


class SearchResponse(BaseModel):
    """Response from a web search operation."""

    status: str = Field(description="Status of the search operation (success or error)")
    query: str = Field(description="Original search query")
    results: List[SearchResult] = Field(description="List of search results")
    metadata: Optional[SearchMetadata] = Field(default=None, description="Metadata about the search")
    error: Optional[str] = Field(default=None, description="Error message if status is error")


class WebContentFetcher:
    """Utility for fetching web content."""

    def fetch_content(self, url: str) -> Optional[str]:
        """Fetch content from a URL.

        Args:
            url: URL to fetch content from

        Returns:
            Content of the page or None if fetching failed
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception:
            return None


class WebSearch:
    """Web search tool that can use multiple search engines."""

    def __init__(
        self,
        preferred_engine: str = "google",
        google_api_key: Optional[str] = None,
        google_cse_id: Optional[str] = None,
        bing_api_key: Optional[str] = None,
    ):
        """Initialize the web search tool.

        Args:
            preferred_engine: Preferred search engine (google, bing, duckduckgo, baidu)
            google_api_key: Google API key (defaults to GOOGLE_API_KEY environment variable)
            google_cse_id: Google Custom Search Engine ID (defaults to GOOGLE_CSE_ID environment variable)
            bing_api_key: Bing API key (defaults to BING_SEARCH_API_KEY environment variable)
        """
        self.preferred_engine = preferred_engine
        self.content_fetcher = WebContentFetcher()
        
        # Initialize search engines
        self.engines = {
            "google": GoogleSearchEngine(api_key=google_api_key, cse_id=google_cse_id),
            "bing": BingSearchEngine(api_key=bing_api_key),
            "duckduckgo": DuckDuckGoSearchEngine(),
            "baidu": BaiduSearchEngine(),
        }

    def search(
        self,
        query: str,
        max_results: int = 5,
        fetch_content: bool = False,
        engine: Optional[str] = None,
    ) -> SearchResponse:
        """Search the web for information.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            fetch_content: Whether to fetch the full content of each result
            engine: Search engine to use (defaults to preferred_engine)

        Returns:
            SearchResponse containing search results
        """
        engine_name = engine or self.preferred_engine
        
        if engine_name not in self.engines:
            return SearchResponse(
                status="error",
                query=query,
                results=[],
                error=f"Unknown search engine: {engine_name}",
            )
        
        try:
            # Perform search using the selected engine
            search_engine = self.engines[engine_name]
            raw_results = search_engine.search(query, num_results=max_results)
            
            # Convert to SearchResult objects
            results = []
            for item in raw_results:
                content = None
                if fetch_content:
                    content = self.content_fetcher.fetch_content(item.url)
                
                results.append(
                    SearchResult(
                        title=item.title,
                        url=item.url,
                        description=item.description or "",
                        raw_content=content,
                    )
                )
            
            return SearchResponse(
                status="success",
                query=query,
                results=results,
                metadata=SearchMetadata(
                    engine=engine_name,
                    query=query,
                    total_results=len(results),
                ),
            )
        
        except Exception as e:
            return SearchResponse(
                status="error",
                query=query,
                results=[],
                error=f"Search failed: {str(e)}",
            )
