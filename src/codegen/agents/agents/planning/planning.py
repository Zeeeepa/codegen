"""
Planning implementation for agentgen.

This module provides planning capabilities for agents.
"""

import json
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

class PlanStepStatus(str, Enum):
    """Status of a plan step."""
    
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    
    @classmethod
    def get_all_statuses(cls) -> list[str]:
        """Return a list of all possible step status values"""
        return [status.value for status in cls]

    @classmethod
    def get_active_statuses(cls) -> list[str]:
        """Return a list of values representing active statuses (not started or in progress)"""
        return [cls.NOT_STARTED.value, cls.IN_PROGRESS.value]

    @classmethod
    def get_status_marks(cls) -> Dict[str, str]:
        """Return a mapping of statuses to their marker symbols"""
        return {
            cls.COMPLETED.value: "[✓]",
            cls.IN_PROGRESS.value: "[→]",
            cls.BLOCKED.value: "[!]",
            cls.NOT_STARTED.value: "[ ]",
        }


class PlanStep:
    """A step in a plan."""
    
    def __init__(
        self,
        description: str,
        order: int,
        status: PlanStepStatus = PlanStepStatus.NOT_STARTED,
        implementation_details: Optional[str] = None,
    ):
        """Initialize a PlanStep.
        
        Args:
            description: Description of the step
            order: Order of the step in the plan
            status: Status of the step
            implementation_details: Optional details about the implementation
        """
        self.id = f"step-{uuid4()}"
        self.description = description
        self.order = order
        self.status = status
        self.implementation_details = implementation_details
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def update_status(self, status: PlanStepStatus, details: Optional[str] = None) -> None:
        """Update the status of the step.
        
        Args:
            status: New status
            details: Optional implementation details
        """
        self.status = status
        if details:
            self.implementation_details = details
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the step to a dictionary.
        
        Returns:
            Dictionary representation of the step
        """
        return {
            "id": self.id,
            "description": self.description,
            "order": self.order,
            "status": self.status,
            "implementation_details": self.implementation_details,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Plan:
    """A plan with steps."""
    
    def __init__(
        self,
        title: str,
        description: str,
        steps: Optional[List[PlanStep]] = None,
    ):
        """Initialize a Plan.
        
        Args:
            title: Title of the plan
            description: Description of the plan
            steps: Optional list of steps
        """
        self.id = f"plan-{uuid4()}"
        self.title = title
        self.description = description
        self.steps = steps or []
        self.step_statuses = []
        self.step_notes = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
        # Initialize step_statuses and step_notes
        for _ in self.steps:
            self.step_statuses.append(PlanStepStatus.NOT_STARTED.value)
            self.step_notes.append("")
    
    def add_step(self, step: PlanStep) -> None:
        """Add a step to the plan.
        
        Args:
            step: The step to add
        """
        self.steps.append(step)
        self.step_statuses.append(PlanStepStatus.NOT_STARTED.value)
        self.step_notes.append("")
        self.updated_at = datetime.now().isoformat()
    
    def get_next_step(self) -> Optional[PlanStep]:
        """Get the next pending step.
        
        Returns:
            The next pending step or None if all steps are completed
        """
        for i, step in enumerate(sorted(self.steps, key=lambda s: s.order)):
            if self.step_statuses[i] == PlanStepStatus.NOT_STARTED.value:
                return step
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        """Get the progress of the plan.
        
        Returns:
            Dictionary with progress information
        """
        total = len(self.steps)
        completed = sum(1 for status in self.step_statuses if status == PlanStepStatus.COMPLETED.value)
        in_progress = sum(1 for status in self.step_statuses if status == PlanStepStatus.IN_PROGRESS.value)
        not_started = sum(1 for status in self.step_statuses if status == PlanStepStatus.NOT_STARTED.value)
        blocked = sum(1 for status in self.step_statuses if status == PlanStepStatus.BLOCKED.value)
        
        completion_percentage = (completed / total) * 100 if total > 0 else 0
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started,
            "blocked": blocked,
            "completion_percentage": completion_percentage,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the plan to a dictionary.
        
        Returns:
            Dictionary representation of the plan
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "step_statuses": self.step_statuses,
            "step_notes": self.step_notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class PlanManager:
    """Manager for plans."""
    
    def __init__(self):
        """Initialize a PlanManager."""
        self.plans = {}
        self.current_plan_id = None
    
    def create_plan(self, title: str, description: str, steps: Optional[List[Dict[str, Any]]] = None) -> Plan:
        """Create a new plan.
        
        Args:
            title: Title of the plan
            description: Description of the plan
            steps: Optional list of step dictionaries
        
        Returns:
            The created plan
        """
        plan_steps = []
        if steps:
            for i, step_dict in enumerate(steps):
                if isinstance(step_dict, str):
                    # Handle case where steps are provided as strings
                    plan_steps.append(
                        PlanStep(
                            description=step_dict,
                            order=i + 1,
                            status=PlanStepStatus.NOT_STARTED,
                        )
                    )
                else:
                    # Handle case where steps are provided as dictionaries
                    plan_steps.append(
                        PlanStep(
                            description=step_dict.get("description", ""),
                            order=i + 1,
                            status=PlanStepStatus(step_dict.get("status", PlanStepStatus.NOT_STARTED.value)),
                            implementation_details=step_dict.get("implementation_details"),
                        )
                    )
        
        plan = Plan(title=title, description=description, steps=plan_steps)
        self.plans[plan.id] = plan
        self.current_plan_id = plan.id
        
        return plan
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Get a plan by ID.
        
        Args:
            plan_id: ID of the plan
        
        Returns:
            The plan or None if not found
        """
        return self.plans.get(plan_id)
    
    def get_current_plan(self) -> Optional[Plan]:
        """Get the current plan.
        
        Returns:
            The current plan or None if no plan is set
        """
        if not self.current_plan_id:
            return None
        return self.plans.get(self.current_plan_id)
    
    def set_current_plan(self, plan_id: str) -> None:
        """Set the current plan.
        
        Args:
            plan_id: ID of the plan to set as current
        """
        if plan_id in self.plans:
            self.current_plan_id = plan_id
    
    def update_step_status(self, plan_id: str, step_index: int, status: str, notes: Optional[str] = None) -> None:
        """Update the status of a step.
        
        Args:
            plan_id: ID of the plan
            step_index: Index of the step
            status: New status
            notes: Optional notes for the step
        """
        plan = self.plans.get(plan_id)
        if not plan:
            return
        
        if step_index < 0 or step_index >= len(plan.steps):
            return
        
        # Update step status
        plan.step_statuses[step_index] = status
        
        # Update step notes if provided
        if notes:
            plan.step_notes[step_index] = notes
        
        plan.updated_at = datetime.now().isoformat()
    
    def generate_progress_report(self, plan_id: Optional[str] = None) -> str:
        """Generate a progress report for a plan.
        
        Args:
            plan_id: Optional ID of the plan. If None, uses the current plan.
        
        Returns:
            A progress report as a string
        """
        if plan_id:
            plan = self.plans.get(plan_id)
        else:
            plan = self.get_current_plan()
        
        if not plan:
            return "No plan found."
        
        progress = plan.get_progress()
        
        report = f"# {plan.title} - Progress Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Add progress summary
        report += "## Progress Summary\n\n"
        report += f"- **Completion:** {progress['completion_percentage']:.1f}%\n"
        report += f"- **Total Steps:** {progress['total']}\n"
        report += f"- **Completed:** {progress['completed']}\n"
        report += f"- **In Progress:** {progress['in_progress']}\n"
        report += f"- **Not Started:** {progress['not_started']}\n"
        report += f"- **Blocked:** {progress['blocked']}\n\n"
        
        # Add progress bar
        progress_bar_length = 30
        completed_chars = int((progress['completion_percentage'] / 100) * progress_bar_length)
        report += "```\n["
        report += "=" * completed_chars
        report += " " * (progress_bar_length - completed_chars)
        report += f"] {progress['completion_percentage']:.1f}%\n```\n\n"
        
        # Add steps status
        report += "## Steps Status\n\n"
        report += "| Step | Status | Notes |\n"
        report += "|------|--------|-------|\n"
        
        status_marks = PlanStepStatus.get_status_marks()
        
        for i, step in enumerate(sorted(plan.steps, key=lambda s: s.order)):
            status = plan.step_statuses[i]
            status_mark = status_marks.get(status, "[ ]")
            notes = plan.step_notes[i] or "N/A"
            report += f"| {step.description} | {status_mark} {status.replace('_', ' ').title()} | {notes} |\n"
        
        return report