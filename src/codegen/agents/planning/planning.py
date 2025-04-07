"""
Planning implementation for codegen.

This module provides planning capabilities for agents.
"""

import time
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

class PlanStepStatus(str, Enum):
    """Status of a plan step."""
    
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    
    @classmethod
    def get_all_statuses(cls) -> list[str]:
        """Return a list of all status values"""
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
        status: str = PlanStepStatus.NOT_STARTED.value,
        notes: str = "",
    ):
        """Initialize a plan step.
        
        Args:
            description: Description of the step
            status: Status of the step
            notes: Additional notes for the step
        """
        self.description = description
        self.status = status
        self.notes = notes
        self.created_at = time.time()
        self.updated_at = time.time()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the step to a dictionary."""
        return {
            "description": self.description,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlanStep":
        """Create a step from a dictionary."""
        step = cls(
            description=data["description"],
            status=data.get("status", PlanStepStatus.NOT_STARTED.value),
            notes=data.get("notes", ""),
        )
        step.created_at = data.get("created_at", time.time())
        step.updated_at = data.get("updated_at", time.time())
        return step

class Plan:
    """A plan with steps."""
    
    def __init__(
        self,
        id: str,
        title: str,
        description: str = "",
        steps: List[PlanStep] = None,
    ):
        """Initialize a plan.
        
        Args:
            id: Unique identifier for the plan
            title: Title of the plan
            description: Description of the plan
            steps: List of steps in the plan
        """
        self.id = id
        self.title = title
        self.description = description
        self.steps = steps or []
        self.created_at = time.time()
        self.updated_at = time.time()
        
    def add_step(self, description: str, status: str = PlanStepStatus.NOT_STARTED.value) -> PlanStep:
        """Add a step to the plan.
        
        Args:
            description: Description of the step
            status: Status of the step
            
        Returns:
            The created step
        """
        step = PlanStep(description=description, status=status)
        self.steps.append(step)
        self.updated_at = time.time()
        return step
        
    def get_progress(self) -> Dict[str, Any]:
        """Get the progress of the plan.
        
        Returns:
            Dictionary with progress information
        """
        total = len(self.steps)
        completed = sum(1 for step in self.steps if step.status == PlanStepStatus.COMPLETED.value)
        in_progress = sum(1 for step in self.steps if step.status == PlanStepStatus.IN_PROGRESS.value)
        blocked = sum(1 for step in self.steps if step.status == PlanStepStatus.BLOCKED.value)
        not_started = sum(1 for step in self.steps if step.status == PlanStepStatus.NOT_STARTED.value)
        
        percentage = (completed / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "blocked": blocked,
            "not_started": not_started,
            "percentage": percentage,
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the plan to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Plan":
        """Create a plan from a dictionary."""
        plan = cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
        )
        plan.steps = [PlanStep.from_dict(step_data) for step_data in data.get("steps", [])]
        plan.created_at = data.get("created_at", time.time())
        plan.updated_at = data.get("updated_at", time.time())
        return plan

class PlanManager:
    """Manager for plans."""
    
    def __init__(self):
        """Initialize a plan manager."""
        self.plans = {}
        
    def create_plan(self, title: str, description: str = "", steps: List[str] = None) -> Plan:
        """Create a new plan.
        
        Args:
            title: Title of the plan
            description: Description of the plan
            steps: List of step descriptions
            
        Returns:
            The created plan
        """
        plan_id = str(uuid4())
        plan = Plan(id=plan_id, title=title, description=description)
        
        if steps:
            for step_desc in steps:
                plan.add_step(description=step_desc)
                
        self.plans[plan_id] = plan
        return plan
        
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """Get a plan by ID.
        
        Args:
            plan_id: ID of the plan to get
            
        Returns:
            The plan or None if not found
        """
        return self.plans.get(plan_id)
        
    def update_plan(self, plan_id: str, title: Optional[str] = None, description: Optional[str] = None) -> Optional[Plan]:
        """Update a plan.
        
        Args:
            plan_id: ID of the plan to update
            title: New title for the plan
            description: New description for the plan
            
        Returns:
            The updated plan or None if not found
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None
            
        if title:
            plan.title = title
            
        if description:
            plan.description = description
            
        plan.updated_at = time.time()
        return plan
        
    def add_step(self, plan_id: str, description: str, status: str = PlanStepStatus.NOT_STARTED.value) -> Optional[PlanStep]:
        """Add a step to a plan.
        
        Args:
            plan_id: ID of the plan to add a step to
            description: Description of the step
            status: Status of the step
            
        Returns:
            The created step or None if the plan is not found
        """
        plan = self.get_plan(plan_id)
        if not plan:
            return None
            
        return plan.add_step(description=description, status=status)
        
    def update_step(self, plan_id: str, step_index: int, status: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Update a step in a plan.
        
        Args:
            plan_id: ID of the plan
            step_index: Index of the step to update
            status: New status for the step
            notes: New notes for the step
            
        Returns:
            True if the step was updated, False otherwise
        """
        plan = self.get_plan(plan_id)
        if not plan or step_index < 0 or step_index >= len(plan.steps):
            return False
            
        step = plan.steps[step_index]
        
        if status:
            step.status = status
            
        if notes:
            step.notes = notes
            
        step.updated_at = time.time()
        plan.updated_at = time.time()
        
        return True
        
    def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan.
        
        Args:
            plan_id: ID of the plan to delete
            
        Returns:
            True if the plan was deleted, False otherwise
        """
        if plan_id in self.plans:
            del self.plans[plan_id]
            return True
        return False