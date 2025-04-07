import asyncio
import json
import re
import time
from typing import List, Optional, Set

from pydantic import BaseModel, Field

from agentgen.extensions.tools.websearch.web_search import SearchResult, WebSearch


# Prompts for LLM interactions
OPTIMIZE_QUERY_PROMPT = """
You are a research assistant helping to optimize a search query for web research.
Your task is to reformulate the given query to be more effective for web searches.
Make it specific, use relevant keywords, and ensure it's clear and concise.

Original query: {query}

Provide only the optimized query text without any explanation or additional formatting.
"""

EXTRACT_INSIGHTS_PROMPT = """
Analyze the following content and extract key insights related to the research query.
For each insight, assess its relevance to the query on a scale of 0.0 to 1.0.

Research query: {query}
Content to analyze:
{content}

Extract up to 3 most important insights from this content. For each insight:
1. Provide the insight content
2. Provide relevance score (0.0-1.0)
"""

GENERATE_FOLLOW_UPS_PROMPT = """
Based on the insights discovered so far, generate follow-up research queries to explore gaps or related areas.
These should help deepen our understanding of the topic.

Original query: {original_query}
Current query: {current_query}
Key insights so far:
{insights}

Generate up to 3 specific follow-up queries that would help address gaps in our current knowledge.
Each query should be concise and focused on a specific aspect of the research topic.
"""

# Constants for insight parsing
DEFAULT_RELEVANCE_SCORE = 1.0
FALLBACK_RELEVANCE_SCORE = 0.7
FALLBACK_CONTENT_LIMIT = 500
# Pattern to detect start of an insight (number., -, *, •) and capture content
INSIGHT_MARKER_PATTERN = re.compile(r"^\s*(?:\d+\.|-|\*|•)\s*(.*)")
# Pattern to detect relevance score, capturing the number (case-insensitive)
RELEVANCE_SCORE_PATTERN = re.compile(r"relevance.*?:.*?(\d\.?\d*)", re.IGNORECASE)


class ResearchInsight(BaseModel):
    """A single insight discovered during research."""

    content: str = Field(description="The insight content")
    source_url: str = Field(description="URL where this insight was found")
    source_title: Optional[str] = Field(default=None, description="Title of the source")
    relevance_score: float = Field(
        default=1.0, description="Relevance score (0.0-1.0)", ge=0.0, le=1.0
    )

    def __str__(self) -> str:
        """Format insight as string with source attribution."""
        source = self.source_title or self.source_url
        return f"{self.content} [Source: {source}]"


class ResearchContext(BaseModel):
    """Research context for tracking research progress."""

    query: str = Field(description="The original research query")
    insights: List[ResearchInsight] = Field(
        default_factory=list, description="Key insights discovered"
    )
    follow_up_queries: List[str] = Field(
        default_factory=list, description="Generated follow-up queries"
    )
    visited_urls: Set[str] = Field(
        default_factory=set, description="URLs visited during research"
    )
    current_depth: int = Field(
        default=0, description="Current depth of research exploration", ge=0
    )
    max_depth: int = Field(
        default=2, description="Maximum depth of research to reach", ge=1
    )


class ResearchSummary(BaseModel):
    """Comprehensive summary of deep research results."""

    query: str = Field(description="The original research query")
    insights: List[ResearchInsight] = Field(
        default_factory=list, description="Key insights discovered"
    )
    visited_urls: Set[str] = Field(
        default_factory=set, description="URLs visited during research"
    )
    depth_reached: int = Field(
        default=0, description="Maximum depth of research reached", ge=0
    )
    output: str = Field(default="", description="Formatted research output")

    def format_output(self) -> str:
        """Format the research summary as a structured string."""
        # Group and sort insights by relevance
        grouped_insights = {
            "Key Findings": [i for i in self.insights if i.relevance_score >= 0.8],
            "Additional Information": [
                i for i in self.insights if 0.5 <= i.relevance_score < 0.8
            ],
            "Supplementary Information": [
                i for i in self.insights if i.relevance_score < 0.5
            ],
        }

        sections = [
            f"# Research: {self.query}\n",
            f"**Sources**: {len(self.visited_urls)} | **Depth**: {self.depth_reached + 1}\n",
        ]

        for section_title, insights in grouped_insights.items():
            if insights:
                sections.append(f"## {section_title}")
                for i, insight in enumerate(insights, 1):
                    sections.extend(
                        [
                            insight.content,
                            f"> Source: [{insight.source_title or 'Link'}]({insight.source_url})\n",
                        ]
                    )

        # Assign the formatted string to the 'output' field
        return "\n".join(sections)


class DeepResearch(BaseModel):
    """Advanced research tool that explores a topic through iterative web searches."""

    llm_client = None
    web_search: WebSearch = WebSearch()

    def __init__(self, llm_client=None):
        super().__init__()
        self.llm_client = llm_client

    async def research(
        self,
        query: str,
        max_depth: int = 2,
        results_per_search: int = 5,
        max_insights: int = 20,
        time_limit_seconds: int = 120,
    ) -> ResearchSummary:
        """Execute deep research on the given query."""
        # Normalize parameters
        max_depth = max(1, min(max_depth, 5))
        results_per_search = max(1, min(results_per_search, 20))

        # Initialize research context and set deadline
        context = ResearchContext(query=query, max_depth=max_depth)
        deadline = time.time() + time_limit_seconds

        try:
            # Initiate research process with optimized query
            optimized_query = await self._generate_optimized_query(query)
            await self._research_graph(
                context=context,
                query=optimized_query,
                results_count=results_per_search,
                deadline=deadline,
            )
        except Exception as e:
            print(f"Research error: {str(e)}")

        # Prepare final summary
        summary = ResearchSummary(
            query=query,
            insights=sorted(
                context.insights, key=lambda x: x.relevance_score, reverse=True
            )[:max_insights],
            visited_urls=context.visited_urls,
            depth_reached=context.current_depth,
        )
        
        # Format the output
        summary.output = summary.format_output()
        return summary

    async def _generate_optimized_query(self, query: str) -> str:
        """Generate an optimized search query using LLM."""
        try:
            # If we have an LLM client, use it to optimize the query
            if self.llm_client:
                prompt = OPTIMIZE_QUERY_PROMPT.format(query=query)
                response = await self.llm_client.generate(prompt)
                optimized_query = response.strip()
                
                if not optimized_query:
                    print("Generated empty optimized query, using original")
                    return query
                    
                print(f"Optimized query: '{optimized_query}'")
                return optimized_query
            else:
                # No LLM client, return original query
                return query
        except Exception as e:
            print(f"Failed to optimize query: {str(e)}")
            return query  # Fall back to original query on error

    async def _research_graph(
        self,
        context: ResearchContext,
        query: str,
        results_count: int,
        deadline: float,
    ) -> None:
        """Run a complete research cycle (search, analyze, generate follow-ups)."""
        # Check termination conditions
        if time.time() >= deadline or context.current_depth >= context.max_depth:
            return

        # Log current research step
        print(f"Research cycle at depth {context.current_depth + 1}")

        # 1. Web search
        search_results = await self._search_web(query, results_count)
        if not search_results:
            return

        # 2. Extract insights
        new_insights = await self._extract_insights(
            context, search_results, context.query, deadline
        )
        if not new_insights:
            return

        # 3. Generate follow-up queries
        follow_up_queries = await self._generate_follow_ups(
            new_insights, query, context.query
        )
        context.follow_up_queries.extend(follow_up_queries)

        # Update depth and proceed to next level
        context.current_depth += 1

        # 4. Continue research with follow-up queries
        if follow_up_queries and context.current_depth < context.max_depth:
            tasks = []  # Create a list to hold the tasks
            for follow_up in follow_up_queries[:2]:  # Limit branching factor
                if time.time() >= deadline:
                    break

                # Create a coroutine for the recursive research call
                task = self._research_graph(
                    context=context,
                    query=follow_up,
                    results_count=max(1, results_count - 1),  # Reduce result count
                    deadline=deadline,
                )
                tasks.append(task)  # Add the task to the list

            # Run all the created tasks concurrently
            if tasks:
                await asyncio.gather(*tasks)

    async def _search_web(self, query: str, results_count: int) -> List[SearchResult]:
        """Perform web search for the given query."""
        try:
            search_response = await self.web_search.search(
                query=query, num_results=results_count, fetch_content=True
            )
            return search_response.results
        except Exception as e:
            print(f"Web search error: {str(e)}")
            return []

    async def _extract_insights(
        self,
        context: ResearchContext,
        results: List[SearchResult],
        original_query: str,
        deadline: float,
    ) -> List[ResearchInsight]:
        """Extract insights from search results."""
        all_insights = []

        for rst in results:
            # Skip if URL already visited or time exceeded
            if rst.url in context.visited_urls or time.time() >= deadline:
                continue

            context.visited_urls.add(rst.url)

            # Skip if no content available
            if not rst.raw_content:
                continue

            # Extract insights using LLM
            insights = await self._analyze_content(
                content=rst.raw_content[:10000],  # Limit content size
                url=rst.url,
                title=rst.title,
                query=original_query,
            )

            all_insights.extend(insights)
            context.insights.extend(insights)

            # Log discovered insights
            print(f"Extracted {len(insights)} insights from {rst.url}")

        return all_insights

    async def _generate_follow_ups(
        self, insights: List[ResearchInsight], current_query: str, original_query: str
    ) -> List[str]:
        """Generate follow-up queries based on insights."""
        if not insights or not self.llm_client:
            return []

        # Format insights for the prompt
        insights_text = "\n".join([f"- {insight.content}" for insight in insights[:5]])

        # Create prompt for generating follow-up queries
        prompt = GENERATE_FOLLOW_UPS_PROMPT.format(
            original_query=original_query,
            current_query=current_query,
            insights=insights_text,
        )

        try:
            # Get follow-up queries from LLM
            response = await self.llm_client.generate(prompt)
            
            # Parse the response to extract queries
            queries = []
            for line in response.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    queries.append(line)
            
            # Ensure we don't return more than 3 queries
            return queries[:3]
        except Exception as e:
            print(f"Error generating follow-up queries: {str(e)}")
            return []

    async def _analyze_content(
        self, content: str, url: str, title: str, query: str
    ) -> List[ResearchInsight]:
        """Extract insights from content based on relevance to query."""
        insights = []
        
        if not self.llm_client:
            # No LLM client, create a basic insight
            insights.append(
                ResearchInsight(
                    content=f"Content from {title or url}",
                    source_url=url,
                    source_title=title,
                    relevance_score=FALLBACK_RELEVANCE_SCORE,
                )
            )
            return insights
            
        try:
            prompt = EXTRACT_INSIGHTS_PROMPT.format(
                query=query, content=content[:5000]  # Limit content size
            )
            
            response = await self.llm_client.generate(prompt)
            
            # Parse the response to extract insights
            current_insight = ""
            current_score = DEFAULT_RELEVANCE_SCORE
            
            for line in response.split("\n"):
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Check for relevance score
                score_match = RELEVANCE_SCORE_PATTERN.search(line)
                if score_match:
                    try:
                        current_score = float(score_match.group(1))
                        current_score = max(0.0, min(1.0, current_score))  # Clamp to 0-1
                    except ValueError:
                        current_score = FALLBACK_RELEVANCE_SCORE
                    continue
                
                # Check for new insight marker
                marker_match = INSIGHT_MARKER_PATTERN.match(line)
                if marker_match:
                    # Save previous insight if exists
                    if current_insight:
                        insights.append(
                            ResearchInsight(
                                content=current_insight,
                                source_url=url,
                                source_title=title,
                                relevance_score=current_score,
                            )
                        )
                        current_score = DEFAULT_RELEVANCE_SCORE
                    
                    # Start new insight
                    current_insight = marker_match.group(1)
                else:
                    # Continue current insight
                    current_insight += " " + line
            
            # Add the last insight if exists
            if current_insight:
                insights.append(
                    ResearchInsight(
                        content=current_insight,
                        source_url=url,
                        source_title=title,
                        relevance_score=current_score,
                    )
                )
                
        except Exception as e:
            print(f"Error analyzing content: {str(e)}")
            # Fallback insight
            insights.append(
                ResearchInsight(
                    content=f"Failed to extract insights from content about {title or url}."[:FALLBACK_CONTENT_LIMIT],
                    source_url=url,
                    source_title=title,
                    relevance_score=FALLBACK_RELEVANCE_SCORE,
                )
            )
            
        return insights


if __name__ == "__main__":
    deep_research = DeepResearch()
    result = asyncio.run(
        deep_research.research(
            "What is deep learning", max_depth=1, results_per_search=2
        )
    )
    print(result.output)
