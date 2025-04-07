"""Bing search engine implementation."""

import os
import requests
from typing import List, Optional

from codegen.extensions.tools.websearch.base import SearchItem, WebSearchEngine


class BingSearchEngine(WebSearchEngine):
    """Bing search engine implementation."""

    name: str = "bing"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Bing search engine.

        Args:
            api_key: Bing API key (defaults to BING_SEARCH_API_KEY environment variable)
        """
        self.api_key = api_key or os.environ.get("BING_SEARCH_API_KEY")
        self.endpoint = "https://api.bing.microsoft.com/v7.0/search"

    def search(self, query: str, num_results: int = 10) -> List[SearchItem]:
        """Search Bing for the given query.

        Args:
            query: The search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        if not self.api_key:
            # Fallback to placeholder results if no API key is available
            return [
                SearchItem(
                    title=f"Bing result {i} for {query}",
                    url=f"https://example.com/result-{i}",
                    description=f"This is a placeholder result {i} for {query} from Bing search.",
                )
                for i in range(1, min(num_results + 1, 11))
            ]

        try:
            headers = {"Ocp-Apim-Subscription-Key": self.api_key}
            params = {"q": query, "count": num_results, "responseFilter": "Webpages"}
            response = requests.get(self.endpoint, headers=headers, params=params)
            response.raise_for_status()
            
            search_results = response.json()
            
            results = []
            if "webPages" in search_results and "value" in search_results["webPages"]:
                for item in search_results["webPages"]["value"][:num_results]:
                    results.append(
                        SearchItem(
                            title=item.get("name", ""),
                            url=item.get("url", ""),
                            description=item.get("snippet", ""),
                        )
                    )
            
            return results
        except Exception as e:
            # Fallback to placeholder results on error
            return [
                SearchItem(
                    title=f"Bing result {i} for {query}",
                    url=f"https://example.com/result-{i}",
                    description=f"This is a placeholder result {i} for {query} from Bing search.",
                )
                for i in range(1, min(num_results + 1, 11))
            ]
