"""Codegen Agent API module.

This module provides interfaces for interacting with AI-powered code generation agents.
It includes classes for different agent types (Agent, ChatAgent, CodeAgent) and utilities
for handling agent messages and state.

Examples:
    Basic usage with the Agent class:
    ```python
    from codegen.agents import Agent

    # Initialize an agent with your API token
    agent = Agent(token="your_api_token", org_id=123)

    # Run the agent with a prompt
    job = agent.run("Create a Python function to calculate Fibonacci numbers")

    # Check the status of the job
    status = agent.get_status()
    print(f"Job status: {status['status']}")
    print(f"Result: {status['result']}")
    ```

    Using the ChatAgent for interactive conversations:
    ```python
    from codegen import Codebase
    from codegen.agents.chat_agent import ChatAgent

    # Initialize a codebase
    codebase = Codebase("path/to/repo")

    # Create a chat agent
    agent = ChatAgent(codebase, model_name="claude-3-5-sonnet-latest")

    # Start a conversation
    response, thread_id = agent.chat("How can I optimize this code?")
    print(response)

    # Continue the conversation with the same thread_id
    follow_up, thread_id = agent.chat("What about memory usage?", thread_id=thread_id)
    print(follow_up)
    ```

    Using the CodeAgent for code generation:
    ```python
    from codegen import Codebase
    from codegen.agents.code_agent import CodeAgent

    # Initialize a codebase
    codebase = Codebase("path/to/repo")

    # Create a code agent
    agent = CodeAgent(codebase, model_name="claude-3-7-sonnet-latest")

    # Generate code based on a prompt
    result = agent.run("Create a function to parse JSON data")
    print(result)
    ```

from codegen.agents.agent import Agent
from codegen.agents.chat_agent import ChatAgent
from codegen.agents.code_agent import CodeAgent

__all__ = ["Agent", "ChatAgent", "CodeAgent"]
