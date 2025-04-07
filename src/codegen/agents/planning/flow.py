"""
Flow management for planning in codegen.

This module provides flow control for executing plans.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable

from codegen.agents.base import BaseAgent
from codegen.agents.planning.planning import PlanStepStatus
from codegen.agents.planning.tools import PlanningTool

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

class PlanningFlow(Flow):
    """Flow for executing planning steps."""
    
    def __init__(self, agents: Dict[str, BaseAgent], planning_tool: PlanningTool, plan_id: str):
        """Initialize a PlanningFlow.
        
        Args:
            agents: Dictionary of agents to use for different steps
            planning_tool: Tool for managing plans
            plan_id: ID of the plan to execute
        """
        super().__init__(name="planning")
        self.agents = agents
        self.planning_tool = planning_tool
        self.active_plan_id = plan_id
        self.default_agent = agents.get("default")
        
    async def execute(self, prompt: str) -> str:
        """Execute the planning flow.
        
        Args:
            prompt: The prompt to execute
            
        Returns:
            The response from the agent
        """
        # Check if we have an active plan
        if not self.active_plan_id or self.active_plan_id not in self.planning_tool.plans:
            # Create a new plan
            plan_result = await self.planning_tool.execute(
                command="create",
                plan_id=self.active_plan_id,
                title=f"Plan for: {prompt[:50]}{'...' if len(prompt) > 50 else ''}",
                description=prompt,
                steps=[]
            )
            
            # Generate initial steps
            system_prompt = f"""
            You are a planning assistant. Create a step-by-step plan to accomplish the following task:
            
            {prompt}
            
            Break this down into 3-7 clear, actionable steps. Each step should be specific and measurable.
            """
            
            # Get steps from the default agent
            steps_response = await self.default_agent.generate(system_prompt)
            
            # Parse steps from the response
            steps = self._parse_steps(steps_response)
            
            # Add steps to the plan
            for step in steps:
                await self.planning_tool.execute(
                    command="add_step",
                    plan_id=self.active_plan_id,
                    step=step
                )
                
            # Get the updated plan
            plan_result = await self.planning_tool.execute(
                command="get",
                plan_id=self.active_plan_id
            )
            
            # Return the plan
            return f"I've created a plan to help with this task:\n\n{plan_result['output']}"
        else:
            # Execute the next step in the plan
            plan_result = await self.planning_tool.execute(
                command="get",
                plan_id=self.active_plan_id
            )
            
            # Find the next step that's not completed
            step_index = -1
            for i, status in enumerate(plan_result.get("step_statuses", [])):
                if status != PlanStepStatus.COMPLETED.value:
                    step_index = i
                    break
                    
            if step_index == -1:
                # All steps are completed
                return f"All steps in the plan have been completed!\n\n{plan_result['output']}"
                
            # Mark the step as in progress
            await self.planning_tool.execute(
                command="mark_step",
                plan_id=self.active_plan_id,
                step_index=step_index,
                step_status=PlanStepStatus.IN_PROGRESS.value
            )
            
            # Execute the step
            step = plan_result["steps"][step_index]
            step_prompt = f"""
            You are working on a plan to accomplish the following task:
            
            {plan_result.get('description', 'No description provided')}
            
            The current step you need to complete is:
            
            {step}
            
            Please complete this step and provide a detailed response.
            """
            
            # Get response from the default agent
            step_response = await self.default_agent.generate(step_prompt)
            
            # Mark the step as completed
            await self.planning_tool.execute(
                command="mark_step",
                plan_id=self.active_plan_id,
                step_index=step_index,
                step_status=PlanStepStatus.COMPLETED.value,
                notes=f"Completed: {step_response[:100]}{'...' if len(step_response) > 100 else ''}"
            )
            
            # Get the updated plan
            plan_result = await self.planning_tool.execute(
                command="get",
                plan_id=self.active_plan_id
            )
            
            # Return the step response and updated plan status
            return f"{step_response}\n\n---\n\nPlan Progress:\n{plan_result['output']}"
    
    def next(self) -> Optional[Dict[str, Any]]:
        """Move to the next step in the flow."""
        if self.current_step >= len(self.steps):
            return None
            
        step = self.steps[self.current_step]
        self.current_step += 1
        return step
        
    def add_step(self, step: Dict[str, Any]) -> None:
        """Add a step to the flow."""
        self.steps.append(step)
        
    def _parse_steps(self, response: str) -> List[str]:
        """Parse steps from a response.
        
        Args:
            response: The response to parse
            
        Returns:
            List of steps
        """
        lines = response.strip().split("\n")
        steps = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for numbered steps or bullet points
            if (line.startswith("Step ") or 
                line.startswith("- ") or 
                (len(line) > 2 and line[0].isdigit() and line[1] == ".")):
                
                # Remove the prefix
                if line.startswith("Step "):
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        step = parts[1].strip()
                    else:
                        step = line
                elif line.startswith("- "):
                    step = line[2:].strip()
                else:
                    step = line[line.find(".")+1:].strip()
                    
                steps.append(step)
                
        return steps