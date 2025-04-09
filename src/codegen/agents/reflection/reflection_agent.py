"""
Reflection agent implementation for codegen.

This module provides an agent that can evaluate outputs and provide feedback.
"""

from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from codegen.agents.base import BaseAgent
from codegen.tools.reflection.reflector import Reflector

class ReflectionAgent(BaseAgent):
    """Agent for evaluating outputs and providing feedback."""

    def __init__(
        self,
        model_provider: str = "anthropic",
        model_name: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        **kwargs: Any,
    ) -> None:
        """Initialize the reflection agent.

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
        self.reflector = Reflector()

    def reflect(
        self,
        content: str,
        criteria: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Reflect on the given content based on criteria.

        Args:
            content: The content to reflect on.
            criteria: The criteria to use for reflection.
            context: Additional context for reflection.

        Returns:
            A dictionary containing the reflection results.
        """
        return self.reflector.reflect(
            content=content,
            criteria=criteria,
            context=context or {},
        )

    def improve(
        self,
        content: str,
        feedback: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Improve content based on feedback.

        Args:
            content: The content to improve.
            feedback: The feedback to use for improvement.
            context: Additional context for improvement.

        Returns:
            The improved content.
        """
        return self.reflector.improve(
            content=content,
            feedback=feedback,
            context=context or {},
        )
