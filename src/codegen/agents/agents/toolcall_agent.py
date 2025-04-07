"""
Tool-calling agent implementation for agentgen.

This module provides an agent that can use tools to accomplish tasks.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from uuid import uuid4

from agentgen.agents.base import BaseAgent

class Tool:
    """A tool that can be used by the agent."""

    def __init__(self, name: str, description: str, func: Callable):
        """Initialize a Tool.

        Args:
            name: Name of the tool
            description: Description of what the tool does
            func: Function to call when the tool is invoked
        """
        self.name = name
        self.description = description
        self.func = func

    def __call__(self, *args, **kwargs):
        """Call the tool function."""
        return self.func(*args, **kwargs)


class ToolCallAgent(BaseAgent):
    """Agent that can use tools to accomplish tasks."""

    def __init__(
        self,
        tools: List[Tool],
        model_provider: str = "anthropic",
        model_name: str = "claude-3-5-sonnet-latest",
        memory: bool = True,
        **kwargs
    ):
        """Initialize a ToolCallAgent.

        Args:
            tools: List of tools available to the agent
            model_provider: The model provider to use (e.g., "anthropic", "openai")
            model_name: Name of the model to use
            memory: Whether to let LLM keep track of the conversation history
            **kwargs: Additional LLM configuration options
        """
        super().__init__(model_provider, model_name, memory, **kwargs)
        self.tools = {tool.name: tool for tool in tools}
        self.message_history = {}

    def run(self, prompt: str, thread_id: Optional[str] = None) -> str:
        """Run the agent with a prompt.

        Args:
            prompt: The prompt to run
            thread_id: Optional thread ID for message history. If None, a new thread is created.

        Returns:
            The agent's response
        """
        if thread_id is None:
            thread_id = str(uuid4())

        # Initialize message history for this thread if it doesn't exist
        if thread_id not in self.message_history:
            self.message_history[thread_id] = []

        # Add the user message to history
        self.message_history[thread_id].append({"role": "user", "content": prompt})

        # TODO: Implement actual tool calling logic
        # This is a placeholder for the actual implementation
        response = f"ToolCall Agent would process: {prompt}"

        # Add the assistant's response to history
        self.message_history[thread_id].append({"role": "assistant", "content": response})

        return response

    def get_chat_history(self, thread_id: str) -> list:
        """Retrieve the chat history for a specific thread.

        Args:
            thread_id: The thread ID to retrieve history for

        Returns:
            List of messages in the conversation history
        """
        return self.message_history.get(thread_id, [])
    
    def add_tool(self, tool: Tool) -> None:
        """Add a new tool to the agent.

        Args:
            tool: The tool to add
        """
        self.tools[tool.name] = tool
    
    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent.

        Args:
            tool_name: Name of the tool to remove
        """
        if tool_name in self.tools:
            del self.tools[tool_name]