import asyncio
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from agentgen.extensions.tools.websearch import (
    WebSearch,
    SearchResponse,
    DeepResearch,
    ResearchSummary,
)


class WebSearchTool(BaseModel):
    """Tool for performing web searches."""

    name: str = "web_search"
    description: str = "Search the web for information on a topic"
    
    async def execute(
        self,
        query: str,
        num_results: int = 5,
        fetch_content: bool = False,
        preferred_engine: str = "google",
    ) -> Dict[str, Any]:
        """
        Execute a web search.
        
        Args:
            query: The search query
            num_results: Number of results to return
            fetch_content: Whether to fetch the full content of each result
            preferred_engine: Preferred search engine (google, bing, duckduckgo, baidu)
            
        Returns:
            Dict containing search results
        """
        search_engine = WebSearch()
        response = await search_engine.search(
            query=query,
            num_results=num_results,
            fetch_content=fetch_content,
            preferred_engine=preferred_engine,
        )
        
        # Convert to a dictionary for the agent
        return {
            "status": response.status,
            "query": response.query,
            "results": [
                {
                    "title": result.title,
                    "url": result.url,
                    "description": result.description,
                    "content": result.raw_content[:1000] + "..." if result.raw_content and len(result.raw_content) > 1000 else result.raw_content,
                }
                for result in response.results
            ],
            "error": response.error,
        }


class DeepResearchTool(BaseModel):
    """Tool for performing deep research on a topic."""

    name: str = "deep_research"
    description: str = "Perform comprehensive research on a topic with multiple searches and content analysis"
    
    async def execute(
        self,
        query: str,
        max_depth: int = 2,
        results_per_search: int = 5,
        time_limit_seconds: int = 120,
    ) -> Dict[str, Any]:
        """
        Execute deep research on a topic.
        
        Args:
            query: The research query
            max_depth: Maximum depth of research (1-5)
            results_per_search: Number of search results to analyze per search
            time_limit_seconds: Maximum execution time in seconds
            
        Returns:
            Dict containing research results and insights
        """
        research_tool = DeepResearch()
        summary = await research_tool.research(
            query=query,
            max_depth=max_depth,
            results_per_search=results_per_search,
            time_limit_seconds=time_limit_seconds,
        )
        
        # Convert to a dictionary for the agent
        return {
            "query": summary.query,
            "insights": [
                {
                    "content": insight.content,
                    "source_url": insight.source_url,
                    "source_title": insight.source_title,
                    "relevance_score": insight.relevance_score,
                }
                for insight in summary.insights
            ],
            "visited_urls": list(summary.visited_urls),
            "depth_reached": summary.depth_reached,
            "formatted_output": summary.output,
        }
