"""
Base agent implementation for codegen.

This module provides the base agent class that all other agents inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

class BaseAgent(ABC):
    """Base class for all agents in codegen."""

    def __init__(
        self,
        model_provider: str = "anthropic",
        model_name: str = "claude-3-5-sonnet-latest",
        memory: bool = True,
        **kwargs
    ):
        """Initialize a BaseAgent.

        Args:
            model_provider: The model provider to use (e.g., "anthropic", "openai")
            model_name: Name of the model to use
            memory: Whether to let LLM keep track of the conversation history
            **kwargs: Additional LLM configuration options. Supported options:
                - temperature: Temperature parameter (0-1)
                - top_p: Top-p sampling parameter (0-1)
                - top_k: Top-k sampling parameter (>= 1)
                - max_tokens: Maximum number of tokens to generate
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.memory = memory
        self.config = kwargs

    @abstractmethod
    def run(self, prompt: str, thread_id: Optional[str] = None) -> str:
        """Run the agent with a prompt.

        Args:
            prompt: The prompt to run
            thread_id: Optional thread ID for message history. If None, a new thread is created.

        Returns:
            The agent's response
        """
        pass

    def chat(self, prompt: str, thread_id: Optional[str] = None) -> tuple[str, str]:
        """Chat with the agent, maintaining conversation history.

        Args:
            prompt: The user message
            thread_id: Optional thread ID for message history. If None, a new thread is created.

        Returns:
            A tuple of (response_content, thread_id) to allow continued conversation
        """
        if thread_id is None:
            thread_id = str(uuid4())
            print(f"Starting new chat thread: {thread_id}")
        else:
            print(f"Continuing chat thread: {thread_id}")

        response = self.run(prompt, thread_id=thread_id)
        return response, thread_id

    @abstractmethod
    def get_chat_history(self, thread_id: str) -> list:
        """Retrieve the chat history for a specific thread.

        Args:
            thread_id: The thread ID to retrieve history for

        Returns:
            List of messages in the conversation history
        """
        pass