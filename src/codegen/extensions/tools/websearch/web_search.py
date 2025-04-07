import asyncio
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, model_validator

from agentgen.extensions.tools.websearch.baidu_search import BaiduSearchEngine
from agentgen.extensions.tools.websearch.bing_search import BingSearchEngine
from agentgen.extensions.tools.websearch.duckduckgo_search import DuckDuckGoSearchEngine
from agentgen.extensions.tools.websearch.google_search import GoogleSearchEngine
from agentgen.extensions.tools.websearch.base import SearchItem, WebSearchEngine


class SearchResult(BaseModel):
    """Represents a single search result returned by a search engine."""

    position: int = Field(description="Position in search results")
    url: str = Field(description="URL of the search result")
    title: str = Field(default="", description="Title of the search result")
    description: str = Field(
        default="", description="Description or snippet of the search result"
    )
    source: str = Field(description="The search engine that provided this result")
    raw_content: Optional[str] = Field(
        default=None, description="Raw content from the search result page if available"
    )

    def __str__(self) -> str:
        """String representation of a search result."""
        return f"{self.title} ({self.url})"


class SearchMetadata(BaseModel):
    """Metadata about the search operation."""

    total_results: int = Field(description="Total number of results found")
    language: str = Field(description="Language code used for the search")
    country: str = Field(description="Country code used for the search")


class SearchResponse(BaseModel):
    """Structured response from the web search tool."""

    status: str = Field(default="success", description="Status of the search operation")
    error: Optional[str] = Field(
        default=None, description="Error message if search failed"
    )
    query: str = Field(description="The search query that was executed")
    results: List[SearchResult] = Field(
        default_factory=list, description="List of search results"
    )
    metadata: Optional[SearchMetadata] = Field(
        default=None, description="Metadata about the search"
    )
    
    def to_string(self) -> str:
        """Convert search response to a formatted string."""
        if self.error:
            return f"Search error: {self.error}"

        result_text = [f"Search results for '{self.query}':"]

        for i, result in enumerate(self.results, 1):
            # Add title with position number
            title = result.title.strip() or "No title"
            result_text.append(f"\n{i}. {title}")

            # Add URL with proper indentation
            result_text.append(f"   URL: {result.url}")

            # Add description if available
            if result.description.strip():
                result_text.append(f"   Description: {result.description}")

            # Add content preview if available
            if result.raw_content:
                content_preview = result.raw_content[:1000].replace("\n", " ").strip()
                if len(result.raw_content) > 1000:
                    content_preview += "..."
                result_text.append(f"   Content: {content_preview}")

        # Add metadata at the bottom if available
        if self.metadata:
            result_text.extend(
                [
                    f"\nMetadata:",
                    f"- Total results: {self.metadata.total_results}",
                    f"- Language: {self.metadata.language}",
                    f"- Country: {self.metadata.country}",
                ]
            )

        return "\n".join(result_text)


class WebContentFetcher:
    """Utility class for fetching web content."""

    @staticmethod
    async def fetch_content(url: str, timeout: int = 10) -> Optional[str]:
        """
        Fetch and extract the main content from a webpage.

        Args:
            url: The URL to fetch content from
            timeout: Request timeout in seconds

        Returns:
            Extracted text content or None if fetching fails
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            # Use asyncio to run requests in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: requests.get(url, headers=headers, timeout=timeout)
            )

            if response.status_code != 200:
                print(f"Failed to fetch content from {url}: HTTP {response.status_code}")
                return None

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "header", "footer", "nav"]):
                script.extract()

            # Get text content
            text = soup.get_text(separator="\n", strip=True)

            # Clean up whitespace and limit size (100KB max)
            text = " ".join(text.split())
            return text[:10000] if text else None

        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            return None


class WebSearch(BaseModel):
    """Search the web for information using various search engines."""

    _search_engines: Dict[str, WebSearchEngine] = {
        "google": GoogleSearchEngine(),
        "baidu": BaiduSearchEngine(),
        "duckduckgo": DuckDuckGoSearchEngine(),
        "bing": BingSearchEngine(),
    }
    content_fetcher: WebContentFetcher = WebContentFetcher()

    async def search(
        self,
        query: str,
        num_results: int = 5,
        lang: str = "en",
        country: str = "us",
        fetch_content: bool = False,
        preferred_engine: str = "google",
    ) -> SearchResponse:
        """
        Execute a Web search and return detailed search results.

        Args:
            query: The search query to submit to the search engine
            num_results: The number of search results to return (default: 5)
            lang: Language code for search results (default: en)
            country: Country code for search results (default: us)
            fetch_content: Whether to fetch content from result pages (default: False)
            preferred_engine: Preferred search engine to use first (default: google)

        Returns:
            A structured response containing search results and metadata
        """
        # Set up search parameters
        search_params = {"lang": lang, "country": country}
        
        # Configure engine order based on preference
        engine_order = self._get_engine_order(preferred_engine)
        
        # Try searching with each engine
        results = await self._try_all_engines(query, num_results, search_params, engine_order)

        if not results:
            # All engines failed
            return SearchResponse(
                status="error",
                error="All search engines failed to return results.",
                query=query,
                results=[],
            )

        # Fetch content if requested
        if fetch_content:
            results = await self._fetch_content_for_results(results)

        # Return a successful structured response
        return SearchResponse(
            status="success",
            query=query,
            results=results,
            metadata=SearchMetadata(
                total_results=len(results),
                language=lang,
                country=country,
            ),
        )

    async def _try_all_engines(
        self, 
        query: str, 
        num_results: int, 
        search_params: Dict[str, Any],
        engine_order: List[str],
    ) -> List[SearchResult]:
        """Try all search engines in the configured order."""
        failed_engines = []

        for engine_name in engine_order:
            if engine_name not in self._search_engines:
                continue
                
            engine = self._search_engines[engine_name]
            print(f"Attempting search with {engine_name.capitalize()}...")
            
            try:
                search_items = await self._perform_search_with_engine(
                    engine, query, num_results, search_params
                )

                if not search_items:
                    failed_engines.append(engine_name)
                    continue

                if failed_engines:
                    print(f"Search successful with {engine_name.capitalize()} after trying: {', '.join(failed_engines)}")

                # Transform search items into structured results
                return [
                    SearchResult(
                        position=i + 1,
                        url=item.url,
                        title=item.title or f"Result {i+1}",  # Ensure we always have a title
                        description=item.description or "",
                        source=engine_name,
                    )
                    for i, item in enumerate(search_items)
                ]
            except Exception as e:
                print(f"Error with {engine_name} search: {str(e)}")
                failed_engines.append(engine_name)
                continue

        if failed_engines:
            print(f"All search engines failed: {', '.join(failed_engines)}")
        return []

    async def _fetch_content_for_results(
        self, results: List[SearchResult]
    ) -> List[SearchResult]:
        """Fetch and add web content to search results."""
        if not results:
            return []

        # Create tasks for each result
        tasks = [self._fetch_single_result_content(result) for result in results]

        # Run tasks concurrently
        fetched_results = await asyncio.gather(*tasks)
        return fetched_results

    async def _fetch_single_result_content(self, result: SearchResult) -> SearchResult:
        """Fetch content for a single search result."""
        if result.url:
            content = await self.content_fetcher.fetch_content(result.url)
            if content:
                result.raw_content = content
        return result

    def _get_engine_order(self, preferred_engine: str = "google") -> List[str]:
        """Determines the order in which to try search engines."""
        # Start with preferred engine if it exists
        engine_order = [preferred_engine] if preferred_engine in self._search_engines else []
        
        # Add remaining engines
        engine_order.extend([e for e in self._search_engines if e not in engine_order])
        
        return engine_order

    async def _perform_search_with_engine(
        self,
        engine: WebSearchEngine,
        query: str,
        num_results: int,
        search_params: Dict[str, Any],
    ) -> List[SearchItem]:
        """Execute search with the given engine and parameters."""
        try:
            # Run the search in a thread pool to avoid blocking
            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: engine.perform_search(
                    query,
                    num_results=num_results,
                    lang=search_params.get("lang"),
                    country=search_params.get("country"),
                ),
            )
        except Exception as e:
            print(f"Search engine error: {str(e)}")
            return []


if __name__ == "__main__":
    web_search = WebSearch()
    search_response = asyncio.run(
        web_search.search(
            query="Python programming", fetch_content=True, num_results=1
        )
    )
    print(search_response.to_string())
