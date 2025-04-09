"""
Research agent implementation for codegen.

This module provides an agent that can research code and provide analysis.
"""

from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from codegen.agents.base import BaseAgent
from codegen.tools.research.researcher import Researcher
from codegen.tools.research.context_understanding import ContextUnderstanding

class ResearchAgent(BaseAgent):
    """Agent for researching code and providing analysis."""

    def __init__(
        self,
        model_provider: str = "anthropic",
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> None:
        """Initialize the research agent.

        Args:
            model_provider: The model provider to use.
            model_name: The model name to use.
            temperature: The temperature to use for generation.
            max_tokens: The maximum number of tokens to generate.
            **kwargs: Additional arguments to pass to the base agent.
        """
        super().__init__(
            model_provider=model_provider,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self.researcher = Researcher()
        self.context_understanding = ContextUnderstanding()

    def research(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        max_results: int = 5,
    ) -> Dict[str, Any]:
        """Research the given query.

        Args:
            query: The query to research.
            context: Additional context for research.
            max_results: Maximum number of results to return.

        Returns:
            A dictionary containing the research results.
        """
        return self.researcher.research(
            query=query,
            context=context or {},
            max_results=max_results,
        )

    def analyze_context(
        self,
        content: str,
        questions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze the given content for context understanding.

        Args:
            content: The content to analyze.
            questions: Specific questions to answer about the content.
            context: Additional context for analysis.

        Returns:
            A dictionary containing the analysis results.
        """
        return self.context_understanding.analyze(
            content=content,
            questions=questions,
            context=context or {},
        )
