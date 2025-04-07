"""
Planning tools for codegen agents.

This module provides tools for creating and managing plans.
"""

from typing import Dict, List, Optional, Any, Union

from codegen.agents.planning.planning import Plan, PlanStep, PlanStepStatus, PlanManager
from codegen.agents.toolcall_agent import Tool

class PlanningTool(Tool):
    """Tool for creating and managing plans."""
    
    def __init__(self):
        """Initialize a PlanningTool."""
        super().__init__(
            name="planning",
            description="Create and manage plans with steps",
            function=self.execute,
        )
        self.plans = {}
        
    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a planning command.
        
        Args:
            command: The command to execute
            **kwargs: Additional arguments for the command
            
        Returns:
            The result of the command
        """
        if command == "create":
            return await self._create_plan(**kwargs)
        elif command == "get":
            return await self._get_plan(**kwargs)
        elif command == "list":
            return await self._list_plans(**kwargs)
        elif command == "update":
            return await self._update_plan(**kwargs)
        elif command == "add_step":
            return await self._add_step(**kwargs)
        elif command == "mark_step":
            return await self._mark_step(**kwargs)
        elif command == "delete":
            return await self._delete_plan(**kwargs)
        else:
            return {"error": f"Unknown command: {command}"}
            
    async def _create_plan(self, plan_id: str, title: str, steps: List[str], description: str = "") -> Dict[str, Any]:
        """Create a new plan.
        
        Args:
            plan_id: ID for the plan
            title: Title of the plan
            steps: List of step descriptions
            description: Optional description of the plan
            
        Returns:
            The created plan
        """
        # Create a new plan
        self.plans[plan_id] = {
            "id": plan_id,
            "title": title,
            "description": description,
            "steps": steps,
            "step_statuses": [PlanStepStatus.NOT_STARTED.value] * len(steps),
            "step_notes": [""] * len(steps),
        }
        
        return {
            "output": f"Created plan '{title}' with {len(steps)} steps",
            "plan_id": plan_id,
        }
        
    async def _get_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get a plan by ID.
        
        Args:
            plan_id: ID of the plan to get
            
        Returns:
            The plan
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
            
        plan_data = self.plans[plan_id]
        title = plan_data["title"]
        steps = plan_data["steps"]
        step_statuses = plan_data["step_statuses"]
        step_notes = plan_data.get("step_notes", [""] * len(steps))
        
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
        
        plan_text = f"Plan: {title} (ID: {plan_id})\n"
        plan_text += "=" * len(plan_text) + "\n\n"
        
        plan_text += f"Progress: {completed}/{total} steps completed ({progress:.1f}%)\n"
        plan_text += f"Status: {status_counts[PlanStepStatus.COMPLETED.value]} completed, {status_counts[PlanStepStatus.IN_PROGRESS.value]} in progress, "
        plan_text += f"{status_counts[PlanStepStatus.BLOCKED.value]} blocked, {status_counts[PlanStepStatus.NOT_STARTED.value]} not started\n\n"
        plan_text += "Steps:\n"
        
        status_marks = PlanStepStatus.get_status_marks()
        
        for i, (step, status, notes) in enumerate(zip(steps, step_statuses, step_notes)):
            # Use status marks to indicate step status
            status_mark = status_marks.get(status, status_marks[PlanStepStatus.NOT_STARTED.value])
            
            plan_text += f"{i}. {status_mark} {step}\n"
            if notes:
                plan_text += f"   Notes: {notes}\n"
                
        return {
            "output": plan_text,
            "plan_id": plan_id,
            "title": title,
            "steps": steps,
            "step_statuses": step_statuses,
            "step_notes": step_notes,
            "progress": progress,
        }
        
    async def _list_plans(self) -> Dict[str, Any]:
        """List all plans.
        
        Returns:
            List of plans
        """
        plans_list = []
        
        for plan_id, plan_data in self.plans.items():
            title = plan_data["title"]
            steps = plan_data["steps"]
            step_statuses = plan_data["step_statuses"]
            
            completed = sum(1 for status in step_statuses if status == PlanStepStatus.COMPLETED.value)
            total = len(steps)
            progress = (completed / total) * 100 if total > 0 else 0
            
            plans_list.append({
                "id": plan_id,
                "title": title,
                "progress": f"{completed}/{total} ({progress:.1f}%)",
            })
            
        return {
            "output": f"Found {len(plans_list)} plans",
            "plans": plans_list,
        }
        
    async def _update_plan(self, plan_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Update a plan.
        
        Args:
            plan_id: ID of the plan to update
            title: Optional new title
            description: Optional new description
            
        Returns:
            The updated plan
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
            
        plan_data = self.plans[plan_id]
        
        if title:
            plan_data["title"] = title
            
        if description:
            plan_data["description"] = description
            
        return {
            "output": f"Updated plan {plan_id}",
            "plan_id": plan_id,
        }
        
    async def _add_step(self, plan_id: str, step: str, index: Optional[int] = None) -> Dict[str, Any]:
        """Add a step to a plan.
        
        Args:
            plan_id: ID of the plan to add a step to
            step: Description of the step
            index: Optional index to insert the step at
            
        Returns:
            The updated plan
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
            
        plan_data = self.plans[plan_id]
        steps = plan_data["steps"]
        step_statuses = plan_data["step_statuses"]
        step_notes = plan_data.get("step_notes", [""] * len(steps))
        
        if index is not None and 0 <= index <= len(steps):
            steps.insert(index, step)
            step_statuses.insert(index, PlanStepStatus.NOT_STARTED.value)
            step_notes.insert(index, "")
        else:
            steps.append(step)
            step_statuses.append(PlanStepStatus.NOT_STARTED.value)
            step_notes.append("")
            
        plan_data["steps"] = steps
        plan_data["step_statuses"] = step_statuses
        plan_data["step_notes"] = step_notes
        
        return {
            "output": f"Added step to plan {plan_id}",
            "plan_id": plan_id,
            "steps": steps,
        }
        
    async def _mark_step(self, plan_id: str, step_index: int, step_status: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Mark a step with a status.
        
        Args:
            plan_id: ID of the plan
            step_index: Index of the step to mark
            step_status: New status for the step
            notes: Optional notes for the step
            
        Returns:
            The updated plan
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
            
        plan_data = self.plans[plan_id]
        steps = plan_data["steps"]
        
        if step_index < 0 or step_index >= len(steps):
            return {"error": f"Step index {step_index} out of range"}
            
        # Ensure step_statuses and step_notes are initialized
        if "step_statuses" not in plan_data:
            plan_data["step_statuses"] = [PlanStepStatus.NOT_STARTED.value] * len(steps)
            
        if "step_notes" not in plan_data:
            plan_data["step_notes"] = [""] * len(steps)
            
        step_statuses = plan_data["step_statuses"]
        step_notes = plan_data["step_notes"]
        
        # Update the status
        if step_status in PlanStepStatus.get_all_statuses():
            step_statuses[step_index] = step_status
        else:
            return {"error": f"Invalid step status: {step_status}"}
            
        # Update notes if provided
        if notes:
            step_notes[step_index] = notes
            
        return {
            "output": f"Marked step {step_index} as {step_status}",
            "plan_id": plan_id,
            "step_index": step_index,
            "step_status": step_status,
        }
        
    async def _delete_plan(self, plan_id: str) -> Dict[str, Any]:
        """Delete a plan.
        
        Args:
            plan_id: ID of the plan to delete
            
        Returns:
            Confirmation of deletion
        """
        if plan_id not in self.plans:
            return {"error": f"Plan with ID {plan_id} not found"}
            
        del self.plans[plan_id]
        
        return {
            "output": f"Deleted plan {plan_id}",
            "plan_id": plan_id,
        }