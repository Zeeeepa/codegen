"""
Planning agent implementation for codegen.

This module provides an agent that can create and execute plans.
"""

from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from codegen.agents.base import BaseAgent
from codegen.agents.planning.planning import PlanManager, PlanStepStatus
from codegen.agents.planning.tools import PlanningTool
from codegen.agents.planning.flow import PlanningFlow

class PlanningAgent(BaseAgent):
    """Agent for creating and executing plans."""

    def __init__(
        self,
        model_provider: str = "anthropic",
        model_name: str = "claude-3-5-sonnet-latest",
        memory: bool = True,
        max_iterations: int = 10,
        **kwargs
    ):
        """Initialize a PlanningAgent.

        Args:
            model_provider: The model provider to use (e.g., "anthropic", "openai")
            model_name: Name of the model to use
            memory: Whether to let LLM keep track of the conversation history
            max_iterations: Maximum number of planning iterations
            **kwargs: Additional LLM configuration options
        """
        super().__init__(model_provider, model_name, memory, **kwargs)
        self.max_iterations = max_iterations
        self.message_history = {}
        self.plan_manager = PlanManager()
        self.planning_tool = PlanningTool()
        self.flows = {}

    async def run(self, prompt: str, thread_id: Optional[str] = None) -> str:
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
            self.flows[thread_id] = PlanningFlow(
                agents={"default": self},
                planning_tool=self.planning_tool,
                plan_id=f"plan_{thread_id}"
            )

        # Add the user message to history
        self.message_history[thread_id].append({"role": "user", "content": prompt})

        # Execute the planning flow
        flow = self.flows[thread_id]
        response = await flow.execute(prompt)

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
    
    def get_plan(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the plan for a specific thread.

        Args:
            thread_id: The thread ID to retrieve the plan for

        Returns:
            The plan as a dictionary or None if no plan exists
        """
        flow = self.flows.get(thread_id)
        if not flow:
            return None
        
        plan_id = flow.active_plan_id
        if not plan_id or plan_id not in self.planning_tool.plans:
            return None
        
        return self.planning_tool.plans[plan_id]