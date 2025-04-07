"""
Planning tools for agentgen.

This module provides tools for planning and plan management.
"""

from typing import Any, Dict, List, Optional, Union

from agentgen.agents.planning.planning import Plan, PlanStep, PlanStepStatus, PlanManager
from agentgen.agents.toolcall_agent import Tool

class PlanningTool:
    """Tool for planning and plan management."""
    
    name: str = "planning"
    description: str = "A planning tool that allows the agent to create and manage plans for solving complex tasks."
    
    def __init__(self):
        """Initialize PlanningTool."""
        self.plans = {}  # Dictionary to store plans by plan_id
        self._current_plan_id = None  # Track the current active plan
    
    def to_param(self) -> Dict[str, Any]:
        """Convert the tool to a parameter dictionary for LLM."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "description": "The command to execute. Available commands: create, update, list, get, set_active, mark_step, delete.",
                            "enum": [
                                "create",
                                "update",
                                "list",
                                "get",
                                "set_active",
                                "mark_step",
                                "delete",
                            ],
                            "type": "string",
                        },
                        "plan_id": {
                            "description": "Unique identifier for the plan. Required for create, update, set_active, and delete commands. Optional for get and mark_step (uses active plan if not specified).",
                            "type": "string",
                        },
                        "title": {
                            "description": "Title for the plan. Required for create command, optional for update command.",
                            "type": "string",
                        },
                        "steps": {
                            "description": "List of plan steps. Required for create command, optional for update command.",
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "step_index": {
                            "description": "Index of the step to update (0-based). Required for mark_step command.",
                            "type": "integer",
                        },
                        "step_status": {
                            "description": "Status to set for a step. Used with mark_step command.",
                            "enum": ["not_started", "in_progress", "completed", "blocked"],
                            "type": "string",
                        },
                        "step_notes": {
                            "description": "Additional notes for a step. Optional for mark_step command.",
                            "type": "string",
                        },
                    },
                    "required": ["command"],
                    "additionalProperties": False,
                }
            }
        }
    
    async def execute(
        self,
        command: str,
        plan_id: Optional[str] = None,
        title: Optional[str] = None,
        steps: Optional[List[str]] = None,
        step_index: Optional[int] = None,
        step_status: Optional[str] = None,
        step_notes: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute the planning tool with the given command and parameters.

        Parameters:
        - command: The operation to perform
        - plan_id: Unique identifier for the plan
        - title: Title for the plan (used with create command)
        - steps: List of steps for the plan (used with create command)
        - step_index: Index of the step to update (used with mark_step command)
        - step_status: Status to set for a step (used with mark_step command)
        - step_notes: Additional notes for a step (used with mark_step command)
        """
        if command == "create":
            return self._create_plan(plan_id, title, steps)
        elif command == "update":
            return self._update_plan(plan_id, title, steps)
        elif command == "list":
            return self._list_plans()
        elif command == "get":
            return self._get_plan(plan_id)
        elif command == "set_active":
            return self._set_active_plan(plan_id)
        elif command == "mark_step":
            return self._mark_step(plan_id, step_index, step_status, step_notes)
        elif command == "delete":
            return self._delete_plan(plan_id)
        else:
            raise ValueError(
                f"Unrecognized command: {command}. Allowed commands are: create, update, list, get, set_active, mark_step, delete"
            )
    
    def _create_plan(
        self, plan_id: Optional[str], title: Optional[str], steps: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Create a new plan with the given ID, title, and steps."""
        if not plan_id:
            raise ValueError("Parameter `plan_id` is required for command: create")

        if plan_id in self.plans:
            raise ValueError(
                f"A plan with ID '{plan_id}' already exists. Use 'update' to modify existing plans."
            )

        if not title:
            raise ValueError("Parameter `title` is required for command: create")

        if not steps or not isinstance(steps, list):
            raise ValueError(
                "Parameter `steps` must be a non-empty list for command: create"
            )

        # Create a new plan with initialized step statuses
        plan = {
            "plan_id": plan_id,
            "title": title,
            "steps": steps,
            "step_statuses": ["not_started"] * len(steps),
            "step_notes": [""] * len(steps),
        }

        self.plans[plan_id] = plan
        self._current_plan_id = plan_id  # Set as active plan

        return {
            "output": f"Plan created successfully with ID: {plan_id}\n\n{self._format_plan(plan)}"
        }
    
    def _update_plan(
        self, plan_id: Optional[str], title: Optional[str], steps: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Update an existing plan with new title or steps."""
        if not plan_id:
            raise ValueError("Parameter `plan_id` is required for command: update")

        if plan_id not in self.plans:
            raise ValueError(f"No plan found with ID: {plan_id}")

        plan = self.plans[plan_id]

        if title:
            plan["title"] = title

        if steps:
            if not isinstance(steps, list):
                raise ValueError(
                    "Parameter `steps` must be a list for command: update"
                )

            # Preserve existing step statuses for unchanged steps
            old_steps = plan["steps"]
            old_statuses = plan["step_statuses"]
            old_notes = plan["step_notes"]

            # Create new step statuses and notes
            new_statuses = []
            new_notes = []

            for i, step in enumerate(steps):
                # If the step exists at the same position in old steps, preserve status and notes
                if i < len(old_steps) and step == old_steps[i]:
                    new_statuses.append(old_statuses[i])
                    new_notes.append(old_notes[i])
                else:
                    new_statuses.append("not_started")
                    new_notes.append("")

            plan["steps"] = steps
            plan["step_statuses"] = new_statuses
            plan["step_notes"] = new_notes

        return {
            "output": f"Plan updated successfully: {plan_id}\n\n{self._format_plan(plan)}"
        }
    
    def _list_plans(self) -> Dict[str, Any]:
        """List all available plans."""
        if not self.plans:
            return {
                "output": "No plans available. Create a plan with the 'create' command."
            }

        output = "Available plans:\n"
        for plan_id, plan in self.plans.items():
            current_marker = " (active)" if plan_id == self._current_plan_id else ""
            completed = sum(
                1 for status in plan["step_statuses"] if status == "completed"
            )
            total = len(plan["steps"])
            progress = f"{completed}/{total} steps completed"
            output += f"• {plan_id}{current_marker}: {plan['title']} - {progress}\n"

        return {"output": output}
    
    def _get_plan(self, plan_id: Optional[str]) -> Dict[str, Any]:
        """Get details of a specific plan."""
        if not plan_id:
            # If no plan_id is provided, use the current active plan
            if not self._current_plan_id:
                raise ValueError(
                    "No active plan. Please specify a plan_id or set an active plan."
                )
            plan_id = self._current_plan_id

        if plan_id not in self.plans:
            raise ValueError(f"No plan found with ID: {plan_id}")

        plan = self.plans[plan_id]
        return {"output": self._format_plan(plan)}
    
    def _set_active_plan(self, plan_id: Optional[str]) -> Dict[str, Any]:
        """Set a plan as the active plan."""
        if not plan_id:
            raise ValueError("Parameter `plan_id` is required for command: set_active")

        if plan_id not in self.plans:
            raise ValueError(f"No plan found with ID: {plan_id}")

        self._current_plan_id = plan_id
        return {
            "output": f"Plan '{plan_id}' is now the active plan.\n\n{self._format_plan(self.plans[plan_id])}"
        }
    
    def _mark_step(
        self,
        plan_id: Optional[str],
        step_index: Optional[int],
        step_status: Optional[str],
        step_notes: Optional[str],
    ) -> Dict[str, Any]:
        """Mark a step with a specific status and optional notes."""
        if not plan_id:
            # If no plan_id is provided, use the current active plan
            if not self._current_plan_id:
                raise ValueError(
                    "No active plan. Please specify a plan_id or set an active plan."
                )
            plan_id = self._current_plan_id

        if plan_id not in self.plans:
            raise ValueError(f"No plan found with ID: {plan_id}")

        if step_index is None:
            raise ValueError("Parameter `step_index` is required for command: mark_step")

        plan = self.plans[plan_id]

        if step_index < 0 or step_index >= len(plan["steps"]):
            raise ValueError(
                f"Invalid step_index: {step_index}. Valid indices range from 0 to {len(plan['steps'])-1}."
            )

        if step_status and step_status not in [
            "not_started",
            "in_progress",
            "completed",
            "blocked",
        ]:
            raise ValueError(
                f"Invalid step_status: {step_status}. Valid statuses are: not_started, in_progress, completed, blocked"
            )

        if step_status:
            plan["step_statuses"][step_index] = step_status

        if step_notes:
            plan["step_notes"][step_index] = step_notes

        return {
            "output": f"Step {step_index} updated in plan '{plan_id}'.\n\n{self._format_plan(plan)}"
        }
    
    def _delete_plan(self, plan_id: Optional[str]) -> Dict[str, Any]:
        """Delete a plan."""
        if not plan_id:
            raise ValueError("Parameter `plan_id` is required for command: delete")

        if plan_id not in self.plans:
            raise ValueError(f"No plan found with ID: {plan_id}")

        del self.plans[plan_id]

        # If the deleted plan was the active plan, clear the active plan
        if self._current_plan_id == plan_id:
            self._current_plan_id = None

        return {"output": f"Plan '{plan_id}' has been deleted."}
    
    def _format_plan(self, plan: Dict) -> str:
        """Format a plan for display."""
        output = f"Plan: {plan['title']} (ID: {plan['plan_id']})\n"
        output += "=" * len(output) + "\n\n"

        # Calculate progress statistics
        total_steps = len(plan["steps"])
        completed = sum(1 for status in plan["step_statuses"] if status == "completed")
        in_progress = sum(
            1 for status in plan["step_statuses"] if status == "in_progress"
        )
        blocked = sum(1 for status in plan["step_statuses"] if status == "blocked")
        not_started = sum(
            1 for status in plan["step_statuses"] if status == "not_started"
        )

        output += f"Progress: {completed}/{total_steps} steps completed "
        if total_steps > 0:
            percentage = (completed / total_steps) * 100
            output += f"({percentage:.1f}%)\n"
        else:
            output += "(0%)\n"

        output += f"Status: {completed} completed, {in_progress} in progress, {blocked} blocked, {not_started} not started\n\n"
        output += "Steps:\n"

        # Add each step with its status and notes
        status_marks = {
            "completed": "[✓]",
            "in_progress": "[→]",
            "blocked": "[!]",
            "not_started": "[ ]",
        }

        for i, (step, status, notes) in enumerate(
            zip(plan["steps"], plan["step_statuses"], plan["step_notes"])
        ):
            status_symbol = status_marks.get(status, "[ ]")
            output += f"{i}. {status_symbol} {step}\n"
            if notes:
                output += f"   Notes: {notes}\n"

        return output


class PlanningTools:
    """Collection of tools for planning."""
    
    def __init__(self, plan_manager: Optional[PlanManager] = None):
        """Initialize PlanningTools.
        
        Args:
            plan_manager: Optional plan manager. If None, a new one is created.
        """
        self.plan_manager = plan_manager or PlanManager()
    
    def get_tools(self) -> List[Tool]:
        """Get all planning tools.
        
        Returns:
            List of planning tools
        """
        return [
            Tool(
                name="create_plan",
                description="Create a new plan with steps",
                func=self.create_plan,
            ),
            Tool(
                name="get_plan",
                description="Get a plan by ID",
                func=self.get_plan,
            ),
            Tool(
                name="get_current_plan",
                description="Get the current plan",
                func=self.get_current_plan,
            ),
            Tool(
                name="set_current_plan",
                description="Set the current plan",
                func=self.set_current_plan,
            ),
            Tool(
                name="add_step_to_plan",
                description="Add a step to a plan",
                func=self.add_step_to_plan,
            ),
            Tool(
                name="update_step_status",
                description="Update the status of a step",
                func=self.update_step_status,
            ),
            Tool(
                name="get_next_step",
                description="Get the next pending step in a plan",
                func=self.get_next_step,
            ),
            Tool(
                name="generate_progress_report",
                description="Generate a progress report for a plan",
                func=self.generate_progress_report,
            ),
        ]
    
    def create_plan(self, title: str, description: str, steps: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Create a new plan.
        
        Args:
            title: Title of the plan
            description: Description of the plan
            steps: Optional list of step dictionaries
        
        Returns:
            Dictionary representation of the created plan
        """
        plan = self.plan_manager.create_plan(title, description, steps)
        return plan.to_dict()
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get a plan by ID.
        
        Args:
            plan_id: ID of the plan
        
        Returns:
            Dictionary representation of the plan or None if not found
        """
        plan = self.plan_manager.get_plan(plan_id)
        if not plan:
            return None
        return plan.to_dict()
    
    def get_current_plan(self) -> Optional[Dict[str, Any]]:
        """Get the current plan.
        
        Returns:
            Dictionary representation of the current plan or None if no plan is set
        """
        plan = self.plan_manager.get_current_plan()
        if not plan:
            return None
        return plan.to_dict()
    
    def set_current_plan(self, plan_id: str) -> Dict[str, Any]:
        """Set the current plan.
        
        Args:
            plan_id: ID of the plan to set as current
        
        Returns:
            Status message
        """
        self.plan_manager.set_current_plan(plan_id)
        return {"status": "success", "message": f"Set current plan to {plan_id}"}
    
    def add_step_to_plan(self, plan_id: str, description: str, order: Optional[int] = None) -> Dict[str, Any]:
        """Add a step to a plan.
        
        Args:
            plan_id: ID of the plan
            description: Description of the step
            order: Optional order of the step. If None, appends to the end.
        
        Returns:
            Status message
        """
        plan = self.plan_manager.get_plan(plan_id)
        if not plan:
            return {"status": "error", "message": f"Plan {plan_id} not found"}
        
        if order is None:
            order = len(plan.steps) + 1
        
        step = PlanStep(description=description, order=order)
        plan.add_step(step)
        
        return {"status": "success", "message": f"Added step to plan {plan_id}", "step_id": step.id}
    
    def update_step_status(self, plan_id: str, step_index: int, status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Update the status of a step.
        
        Args:
            plan_id: ID of the plan
            step_index: Index of the step
            status: New status (not_started, in_progress, completed, blocked)
            notes: Optional notes for the step
        
        Returns:
            Status message
        """
        try:
            self.plan_manager.update_step_status(plan_id, step_index, status, notes)
            return {"status": "success", "message": f"Updated step {step_index} in plan {plan_id}"}
        except ValueError as e:
            return {"status": "error", "message": str(e)}
    
    def get_next_step(self, plan_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get the next pending step in a plan.
        
        Args:
            plan_id: Optional ID of the plan. If None, uses the current plan.
        
        Returns:
            Dictionary representation of the next step or None if all steps are completed
        """
        if plan_id:
            plan = self.plan_manager.get_plan(plan_id)
        else:
            plan = self.plan_manager.get_current_plan()
        
        if not plan:
            return None
        
        step = plan.get_next_step()
        if not step:
            return None
        
        return step.to_dict()
    
    def generate_progress_report(self, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a progress report for a plan.
        
        Args:
            plan_id: Optional ID of the plan. If None, uses the current plan.
        
        Returns:
            Dictionary with the progress report
        """
        report = self.plan_manager.generate_progress_report(plan_id)
        return {"report": report}