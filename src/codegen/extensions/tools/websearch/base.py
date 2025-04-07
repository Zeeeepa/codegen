"""Base classes for web search engines."""

from typing import List, Optional

from pydantic import BaseModel, Field


class SearchItem(BaseModel):
    """Represents a single search result item."""

    title: str = Field(description="The title of the search result")
    url: str = Field(description="The URL of the search result")
    description: Optional[str] = Field(
        default=None, description="A description or snippet of the search result"
    )

    def __str__(self) -> str:
        """String representation of a search result item."""
        return f"{self.title} - {self.url}"


class WebSearchEngine(BaseModel):
    """Base class for web search engines."""

    name: str = "base"
    model_config = {"arbitrary_types_allowed": True}

    def search(self, query: str, num_results: int = 10) -> List[SearchItem]:
        """Perform a web search and return a list of search items.

        Args:
            query: The search query to submit to the search engine
            num_results: The number of search results to return (default: 10)

        Returns:
            List of SearchItem objects matching the search query
        """
        raise NotImplementedError("Subclasses must implement search method")
