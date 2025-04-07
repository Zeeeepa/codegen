"""
Flow management for planning in agentgen.

This module provides flow control for executing plans.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable

from agentgen.agents.base import BaseAgent
from agentgen.agents.planning.planning import PlanStepStatus
from agentgen.agents.planning.tools import PlanningTool

class Flow(ABC):
    """Base class for flow control in planning."""

    def __init__(self, name: str):
        """Initialize a Flow.

        Args:
            name: Name of the flow
        """
        self.name = name
        self.steps = []
        self.current_step = 0
        self.state = {}

    @abstractmethod
    def next(self) -> Optional[Dict[str, Any]]:
        """Move to the next step in the flow.

        Returns:
            The next step or None if the flow is complete
        """
        pass

    @abstractmethod
    def add_step(self, step: Dict[str, Any]) -> None:
        """Add a step to the flow.

        Args:
            step: The step to add
        """
        pass

    def reset(self) -> None:
        """Reset the flow to the beginning."""
        self.current_step = 0
        self.state = {}

    def get_state(self) -> Dict[str, Any]:
        """Get the current state of the flow.

        Returns:
            The current state
        """
        return self.state

    def set_state(self, state: Dict[str, Any]) -> None:
        """Set the state of the flow.

        Args:
            state: The state to set
        """
        self.state = state


class LinearFlow(Flow):
    """A linear flow that executes steps in sequence."""

    def __init__(self, name: str):
        """Initialize a LinearFlow.

        Args:
            name: Name of the flow
        """
        super().__init__(name)

    def next(self) -> Optional[Dict[str, Any]]:
        """Move to the next step in the flow.

        Returns:
            The next step or None if the flow is complete
        """
        if self.current_step >= len(self.steps):
            return None

        step = self.steps[self.current_step]
        self.current_step += 1
        return step

    def add_step(self, step: Dict[str, Any]) -> None:
        """Add a step to the flow.

        Args:
            step: The step to add
        """
        self.steps.append(step)


class ConditionalFlow(Flow):
    """A flow that can branch based on conditions."""

    def __init__(self, name: str):
        """Initialize a ConditionalFlow.

        Args:
            name: Name of the flow
        """
        super().__init__(name)
        self.conditions = []

    def next(self) -> Optional[Dict[str, Any]]:
        """Move to the next step in the flow based on conditions.

        Returns:
            The next step or None if the flow is complete
        """
        if self.current_step >= len(self.steps):
            return None

        step = self.steps[self.current_step]
        condition = self.conditions[self.current_step]

        if condition(self.state):
            self.current_step += 1
            return step
        else:
            # Skip this step and move to the next one
            self.current_step += 1
            return self.next()

    def add_step(self, step: Dict[str, Any], condition: Callable[[Dict[str, Any]], bool] = lambda _: True) -> None:
        """Add a step to the flow with a condition.

        Args:
            step: The step to add
            condition: A function that takes the state and returns True if the step should be executed
        """
        self.steps.append(step)
        self.conditions.append(condition)


class PlanningFlow:
    """A flow that manages planning and execution of tasks using agents."""

    def __init__(
        self, 
        agents: Union[BaseAgent, List[BaseAgent], Dict[str, BaseAgent]], 
        planning_tool: Optional[PlanningTool] = None,
        executor_keys: Optional[List[str]] = None,
        plan_id: Optional[str] = None,
    ):
        """Initialize a PlanningFlow.
        
        Args:
            agents: The agent(s) to use for planning and execution
            planning_tool: Optional planning tool to use
            executor_keys: Optional list of agent keys to use as executors
            plan_id: Optional plan ID to use
        """
        # Process agents into a dictionary
        if isinstance(agents, BaseAgent):
            self.agents = {"default": agents}
        elif isinstance(agents, list):
            self.agents = {f"agent_{i}": agent for i, agent in enumerate(agents)}
        else:
            self.agents = agents
            
        # Set primary agent key
        self.primary_agent_key = next(iter(self.agents)) if self.agents else None
        
        # Initialize planning tool
        self.planning_tool = planning_tool or PlanningTool()
        
        # Set executor keys
        self.executor_keys = executor_keys or list(self.agents.keys())
        
        # Set plan ID
        self.active_plan_id = plan_id or f"plan_{int(time.time())}"
        
        # Initialize current step index
        self.current_step_index = None
    
    @property
    def primary_agent(self) -> Optional[BaseAgent]:
        """Get the primary agent for the flow."""
        return self.agents.get(self.primary_agent_key)
    
    def get_executor(self, step_type: Optional[str] = None) -> BaseAgent:
        """
        Get an appropriate executor agent for the current step.
        Can be extended to select agents based on step type/requirements.
        """
        # If step type is provided and matches an agent key, use that agent
        if step_type and step_type in self.agents:
            return self.agents[step_type]

        # Otherwise use the first available executor or fall back to primary agent
        for key in self.executor_keys:
            if key in self.agents:
                return self.agents[key]

        # Fallback to primary agent
        return self.primary_agent
    
    async def execute(self, input_text: str) -> str:
        """Execute the planning flow with agents."""
        try:
            if not self.primary_agent:
                raise ValueError("No primary agent available")

            # Create initial plan if input provided
            if input_text:
                await self._create_initial_plan(input_text)

                # Verify plan was created successfully
                if self.active_plan_id not in self.planning_tool.plans:
                    return f"Failed to create plan for: {input_text}"

            result = ""
            while True:
                # Get current step to execute
                self.current_step_index, step_info = await self._get_current_step_info()

                # Exit if no more steps or plan completed
                if self.current_step_index is None:
                    result += await self._finalize_plan()
                    break

                # Execute current step with appropriate agent
                step_type = step_info.get("type") if step_info else None
                executor = self.get_executor(step_type)
                step_result = await self._execute_step(executor, step_info)
                result += step_result + "\n"

            return result
        except Exception as e:
            return f"Execution failed: {str(e)}"
    
    async def _create_initial_plan(self, request: str) -> None:
        """Create an initial plan based on the request."""
        # Create a system message for plan creation
        system_message = "You are a planning assistant. Create a concise, actionable plan with clear steps. " \
                         "Focus on key milestones rather than detailed sub-steps. " \
                         "Optimize for clarity and efficiency."

        # Create a user message with the request
        user_message = f"Create a reasonable plan with clear steps to accomplish the task: {request}"

        # Use the primary agent to create a plan
        plan_response = await self.primary_agent.run(
            f"{system_message}\n\n{user_message}"
        )
        
        # Extract steps from the response
        steps = self._extract_steps_from_text(plan_response)
        
        # Create the plan using the planning tool
        await self.planning_tool.execute(
            command="create",
            plan_id=self.active_plan_id,
            title=f"Plan for: {request[:50]}{'...' if len(request) > 50 else ''}",
            steps=steps if steps else ["Analyze request", "Execute task", "Verify results"],
        )
    
    def _extract_steps_from_text(self, text: str) -> List[str]:
        """Extract steps from text."""
        steps = []
        lines = text.split("\n")
        
        for line in lines:
            line = line.strip()
            # Look for numbered steps or bullet points
            if (line.startswith("- ") or 
                line.startswith("* ") or 
                line.startswith("• ") or
                (line[0].isdigit() and line[1:].startswith(". ") or line[1:].startswith(") "))):
                
                # Remove the prefix
                if line.startswith("- ") or line.startswith("* ") or line.startswith("• "):
                    step = line[2:].strip()
                else:
                    # For numbered steps, find the first space after the number
                    first_space = line.find(" ")
                    if first_space != -1:
                        step = line[first_space + 1:].strip()
                    else:
                        continue
                
                if step:
                    steps.append(step)
        
        return steps
    
    async def _get_current_step_info(self) -> tuple[Optional[int], Optional[dict]]:
        """
        Parse the current plan to identify the first non-completed step's index and info.
        Returns (None, None) if no active step is found.
        """
        if (
            not self.active_plan_id
            or self.active_plan_id not in self.planning_tool.plans
        ):
            return None, None

        try:
            # Direct access to plan data from planning tool storage
            plan_data = self.planning_tool.plans[self.active_plan_id]
            steps = plan_data.get("steps", [])
            step_statuses = plan_data.get("step_statuses", [])

            # Find first non-completed step
            for i, step in enumerate(steps):
                if i >= len(step_statuses):
                    status = PlanStepStatus.NOT_STARTED.value
                else:
                    status = step_statuses[i]

                if status in [PlanStepStatus.NOT_STARTED.value, PlanStepStatus.IN_PROGRESS.value]:
                    # Extract step type/category if available
                    step_info = {"text": step}

                    # Try to extract step type from the text (e.g., [SEARCH] or [CODE])
                    import re

                    type_match = re.search(r"\[([A-Z_]+)\]", step)
                    if type_match:
                        step_info["type"] = type_match.group(1).lower()

                    # Mark current step as in_progress
                    try:
                        await self.planning_tool.execute(
                            command="mark_step",
                            plan_id=self.active_plan_id,
                            step_index=i,
                            step_status=PlanStepStatus.IN_PROGRESS.value,
                        )
                    except Exception:
                        # Update step status directly if needed
                        if i < len(step_statuses):
                            step_statuses[i] = PlanStepStatus.IN_PROGRESS.value
                        else:
                            while len(step_statuses) < i:
                                step_statuses.append(PlanStepStatus.NOT_STARTED.value)
                            step_statuses.append(PlanStepStatus.IN_PROGRESS.value)

                        plan_data["step_statuses"] = step_statuses

                    return i, step_info

            return None, None  # No active step found

        except Exception:
            return None, None
    
    async def _execute_step(self, executor: BaseAgent, step_info: dict) -> str:
        """Execute the current step with the specified agent."""
        # Prepare context for the agent with current plan status
        plan_status = await self._get_plan_text()
        step_text = step_info.get("text", f"Step {self.current_step_index}")

        # Create a prompt for the agent to execute the current step
        step_prompt = f"""
        CURRENT PLAN STATUS:
        {plan_status}

        YOUR CURRENT TASK:
        You are now working on step {self.current_step_index}: "{step_text}"

        Please execute this step using the appropriate tools. When you're done, provide a summary of what you accomplished.
        """

        # Use agent.run() to execute the step
        try:
            step_result = await executor.run(step_prompt)

            # Mark the step as completed after successful execution
            await self._mark_step_completed()

            return step_result
        except Exception as e:
            return f"Error executing step {self.current_step_index}: {str(e)}"
    
    async def _mark_step_completed(self) -> None:
        """Mark the current step as completed."""
        if self.current_step_index is None:
            return

        try:
            # Mark the step as completed
            await self.planning_tool.execute(
                command="mark_step",
                plan_id=self.active_plan_id,
                step_index=self.current_step_index,
                step_status=PlanStepStatus.COMPLETED.value,
            )
        except Exception:
            # Update step status directly in planning tool storage
            if self.active_plan_id in self.planning_tool.plans:
                plan_data = self.planning_tool.plans[self.active_plan_id]
                step_statuses = plan_data.get("step_statuses", [])

                # Ensure the step_statuses list is long enough
                while len(step_statuses) <= self.current_step_index:
                    step_statuses.append(PlanStepStatus.NOT_STARTED.value)

                # Update the status
                step_statuses[self.current_step_index] = PlanStepStatus.COMPLETED.value
                plan_data["step_statuses"] = step_statuses
    
    async def _get_plan_text(self) -> str:
        """Get the current plan as formatted text."""
        try:
            result = await self.planning_tool.execute(
                command="get", plan_id=self.active_plan_id
            )
            return result.get("output", "")
        except Exception:
            return self._generate_plan_text_from_storage()
    
    def _generate_plan_text_from_storage(self) -> str:
        """Generate plan text directly from storage if the planning tool fails."""
        try:
            if self.active_plan_id not in self.planning_tool.plans:
                return f"Error: Plan with ID {self.active_plan_id} not found"

            plan_data = self.planning_tool.plans[self.active_plan_id]
            title = plan_data.get("title", "Untitled Plan")
            steps = plan_data.get("steps", [])
            step_statuses = plan_data.get("step_statuses", [])
            step_notes = plan_data.get("step_notes", [])

            # Ensure step_statuses and step_notes match the number of steps
            while len(step_statuses) < len(steps):
                step_statuses.append(PlanStepStatus.NOT_STARTED.value)
            while len(step_notes) < len(steps):
                step_notes.append("")

            # Count steps by status
            status_counts = {
                PlanStepStatus.NOT_STARTED.value: 0,
                PlanStepStatus.IN_PROGRESS.value: 0,
                PlanStepStatus.COMPLETED.value: 0,
                PlanStepStatus.BLOCKED.value: 0,
            }

            for status in step_statuses:
                if status in status_counts:
                    status_counts[status] += 1

            completed = status_counts[PlanStepStatus.COMPLETED.value]
            total = len(steps)
            progress = (completed / total) * 100 if total > 0 else 0

            plan_text = f"Plan: {title} (ID: {self.active_plan_id})\n"
            plan_text += "=" * len(plan_text) + "\n\n"

            plan_text += (
                f"Progress: {completed}/{total} steps completed ({progress:.1f}%)\n"
            )
            plan_text += f"Status: {status_counts[PlanStepStatus.COMPLETED.value]} completed, {status_counts[PlanStepStatus.IN_PROGRESS.value]} in progress, "
            plan_text += f"{status_counts[PlanStepStatus.BLOCKED.value]} blocked, {status_counts[PlanStepStatus.NOT_STARTED.value]} not started\n\n"
            plan_text += "Steps:\n"

            status_marks = {
                PlanStepStatus.COMPLETED.value: "[✓]",
                PlanStepStatus.IN_PROGRESS.value: "[→]",
                PlanStepStatus.BLOCKED.value: "[!]",
                PlanStepStatus.NOT_STARTED.value: "[ ]",
            }

            for i, (step, status, notes) in enumerate(
                zip(steps, step_statuses, step_notes)
            ):
                # Use status marks to indicate step status
                status_mark = status_marks.get(
                    status, status_marks[PlanStepStatus.NOT_STARTED.value]
                )

                plan_text += f"{i}. {status_mark} {step}\n"
                if notes:
                    plan_text += f"   Notes: {notes}\n"

            return plan_text
        except Exception as e:
            return f"Error: Unable to retrieve plan with ID {self.active_plan_id}"
    
    async def _finalize_plan(self) -> str:
        """Finalize the plan and provide a summary."""
        plan_text = await self._get_plan_text()

        # Create a summary using the primary agent
        try:
            summary_prompt = f"""
            The plan has been completed. Here is the final plan status:

            {plan_text}

            Please provide a summary of what was accomplished and any final thoughts.
            """
            summary = await self.primary_agent.run(summary_prompt)
            return f"Plan completed:\n\n{summary}"
        except Exception as e:
            return "Plan completed. Error generating summary."