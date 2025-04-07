"""Web search tool for the codegen extensions."""

from typing import Optional, List, Dict, Any

from langchain_core.tools import BaseTool

from codegen.extensions.tools.websearch import (
    WebSearch,
    DeepResearch,
    SearchResult,
    ResearchInsight,
    ResearchSummary,
)


class WebSearchTool(BaseTool):
    """Tool for searching the web."""

    name = "web_search"
    description = "Search the web for information on a topic."

    def _run(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Run the web search tool.

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        search = WebSearch()
        results = search.search(query, max_results=max_results)
        return results.results


class DeepResearchTool(BaseTool):
    """Tool for conducting deep research on a topic."""

    name = "deep_research"
    description = "Conduct deep research on a topic, analyzing multiple sources."

    def _run(self, topic: str, max_sources: int = 5, depth: str = "medium") -> Dict[str, Any]:
        """Run the deep research tool.

        Args:
            topic: The research topic
            max_sources: Maximum number of sources to analyze
            depth: Research depth (shallow, medium, deep)

        Returns:
            Research summary and insights
        """
        research = DeepResearch()
        result = research.research(topic, max_sources=max_sources, depth=depth)
        return {
            "summary": result.summary,
            "insights": result.insights,
            "sources": result.sources,
        }
