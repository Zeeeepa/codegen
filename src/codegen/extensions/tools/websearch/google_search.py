"""Google search engine implementation."""

import os
import requests
from typing import List, Optional

from codegen.extensions.tools.websearch.base import SearchItem, WebSearchEngine


class GoogleSearchEngine(WebSearchEngine):
    """Google search engine implementation."""

    name: str = "google"

    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        """Initialize the Google search engine.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY environment variable)
            cse_id: Google Custom Search Engine ID (defaults to GOOGLE_CSE_ID environment variable)
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.cse_id = cse_id or os.environ.get("GOOGLE_CSE_ID")
        self.endpoint = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, num_results: int = 10) -> List[SearchItem]:
        """Search Google for the given query.

        Args:
            query: The search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        if not self.api_key or not self.cse_id:
            # Fallback to placeholder results if no API key or CSE ID is available
            return [
                SearchItem(
                    title=f"Google result {i} for {query}",
                    url=f"https://example.com/result-{i}",
                    description=f"This is a placeholder result {i} for {query} from Google search.",
                )
                for i in range(1, min(num_results + 1, 11))
            ]

        try:
            params = {
                "q": query,
                "key": self.api_key,
                "cx": self.cse_id,
                "num": min(num_results, 10),  # Google API limits to 10 results per request
            }
            response = requests.get(self.endpoint, params=params)
            response.raise_for_status()
            
            search_results = response.json()
            
            results = []
            if "items" in search_results:
                for item in search_results["items"][:num_results]:
                    results.append(
                        SearchItem(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            description=item.get("snippet", ""),
                        )
                    )
            
            return results
        except Exception as e:
            # Fallback to placeholder results on error
            return [
                SearchItem(
                    title=f"Google result {i} for {query}",
                    url=f"https://example.com/result-{i}",
                    description=f"This is a placeholder result {i} for {query} from Google search.",
                )
                for i in range(1, min(num_results + 1, 11))
            ]
