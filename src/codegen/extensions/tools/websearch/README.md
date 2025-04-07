# Web Search Tools for AgentGen

This module provides web search capabilities for AgentGen agents, allowing them to search the internet for information and perform deep research on topics.

## Features

- Multiple search engine support (Google, Bing, DuckDuckGo, Baidu)
- Automatic fallback between search engines
- Content extraction from web pages
- Deep research with iterative searches and insight extraction
- Structured search results with metadata

## Components

- `WebSearchEngine`: Base class for search engines
- `SearchItem`: Represents a single search result
- `WebSearch`: Main search interface with multiple engine support
- `DeepResearch`: Advanced research tool for comprehensive topic exploration

## Usage

### Basic Web Search

```python
from agentgen.extensions.tools.websearch import WebSearch

# Create a search instance
search_tool = WebSearch()

# Perform a search
results = await search_tool.search(
    query="artificial intelligence trends",
    num_results=5,
    fetch_content=True,
    preferred_engine="google"
)

# Access the results
for result in results.results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Description: {result.description}")
    if result.raw_content:
        print(f"Content preview: {result.raw_content[:100]}...")
    print("---")
```

### Deep Research

```python
from agentgen.extensions.tools.websearch import DeepResearch

# Create a deep research instance
research_tool = DeepResearch()

# Perform deep research
summary = await research_tool.research(
    query="quantum computing applications",
    max_depth=2,
    results_per_search=5,
    time_limit_seconds=120
)

# Access the research summary
print(f"Research on: {summary.query}")
print(f"Sources visited: {len(summary.visited_urls)}")
print(f"Depth reached: {summary.depth_reached}")

# Print insights
for insight in summary.insights:
    print(f"- {insight.content}")
    print(f"  Source: {insight.source_title or insight.source_url}")
    print(f"  Relevance: {insight.relevance_score}")
```

## Dependencies

See `requirements.txt` for the required dependencies.
