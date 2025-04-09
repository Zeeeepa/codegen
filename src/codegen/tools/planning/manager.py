"""
Planning manager for codegen agents.

This module provides tools for creating and managing plans.
"""

from typing import Dict, List, Optional, Any, Union

class Step:
    """A step in a project plan."""
    
    def __init__(self, id: str, description: str, status: str = "not_started"):
        """Initialize a Step.
        
        Args:
            id: ID of the step
            description: Description of the step
            status: Status of the step
        """
        self.id = id
        self.description = description
        self.status = status
        self.details = ""
        self.pr_number = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "details": self.details,
            "pr_number": self.pr_number,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        """Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Step object
        """
        step = cls(
            id=data["id"],
            description=data["description"],
            status=data["status"],
        )
        step.details = data.get("details", "")
        step.pr_number = data.get("pr_number")
        return step

class Requirement:
    """A requirement in a project plan."""
    
    def __init__(self, id: str, description: str, status: str = "not_started"):
        """Initialize a Requirement.
        
        Args:
            id: ID of the requirement
            description: Description of the requirement
            status: Status of the requirement
        """
        self.id = id
        self.description = description
        self.status = status
        self.details = ""
        self.pr_number = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "details": self.details,
            "pr_number": self.pr_number,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Requirement":
        """Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Requirement object
        """
        req = cls(
            id=data["id"],
            description=data["description"],
            status=data["status"],
        )
        req.details = data.get("details", "")
        req.pr_number = data.get("pr_number")
        return req

class ProjectPlan:
    """A project plan with requirements and steps."""
    
    def __init__(self, title: str, description: str = ""):
        """Initialize a ProjectPlan.
        
        Args:
            title: Title of the plan
            description: Description of the plan
        """
        self.title = title
        self.description = description
        self.requirements = []
        self.steps = []
        
    def add_requirement(self, requirement: Requirement) -> None:
        """Add a requirement to the plan.
        
        Args:
            requirement: Requirement to add
        """
        self.requirements.append(requirement)
        
    def add_step(self, step: Step) -> None:
        """Add a step to the plan.
        
        Args:
            step: Step to add
        """
        self.steps.append(step)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "title": self.title,
            "description": self.description,
            "requirements": [req.to_dict() for req in self.requirements],
            "steps": [step.to_dict() for step in self.steps],
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectPlan":
        """Create from dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            ProjectPlan object
        """
        plan = cls(
            title=data["title"],
            description=data["description"],
        )
        
        for req_data in data.get("requirements", []):
            plan.add_requirement(Requirement.from_dict(req_data))
            
        for step_data in data.get("steps", []):
            plan.add_step(Step.from_dict(step_data))
            
        return plan

class PlanManager:
    """Manager for project plans."""
    
    def __init__(self):
        """Initialize a PlanManager."""
        self.current_plan = None
        
    def create_plan(self, title: str, description: str = "") -> ProjectPlan:
        """Create a new project plan.
        
        Args:
            title: Title of the plan
            description: Description of the plan
            
        Returns:
            The created plan
        """
        self.current_plan = ProjectPlan(title, description)
        return self.current_plan
        
    def load_current_plan(self) -> Optional[ProjectPlan]:
        """Load the current plan.
        
        Returns:
            The current plan, or None if no plan exists
        """
        return self.current_plan
        
    def get_next_step(self) -> Optional[Step]:
        """Get the next pending step in the current plan.
        
        Returns:
            The next step, or None if no steps are pending
        """
        if not self.current_plan:
            return None
            
        for step in self.current_plan.steps:
            if step.status == "not_started":
                return step
                
        return None
        
    def update_step_status(self, step_id: str, status: str, pr_number: Optional[int] = None, details: Optional[str] = None) -> None:
        """Update the status of a step in the current plan.
        
        Args:
            step_id: ID of the step to update
            status: New status for the step
            pr_number: Optional PR number associated with the step
            details: Optional details about the status update
        """
        if not self.current_plan:
            return
            
        for step in self.current_plan.steps:
            if step.id == step_id:
                step.status = status
                if pr_number:
                    step.pr_number = pr_number
                if details:
                    step.details = details
                break
                
    def update_requirement_status(self, req_id: str, status: str, pr_number: Optional[int] = None, details: Optional[str] = None) -> None:
        """Update the status of a requirement in the current plan.
        
        Args:
            req_id: ID of the requirement to update
            status: New status for the requirement
            pr_number: Optional PR number associated with the requirement
            details: Optional details about the status update
        """
        if not self.current_plan:
            return
            
        for req in self.current_plan.requirements:
            if req.id == req_id:
                req.status = status
                if pr_number:
                    req.pr_number = pr_number
                if details:
                    req.details = details
                break
                
    def generate_progress_report(self) -> str:
        """Generate a progress report for the current plan.
        
        Returns:
            Progress report as a string
        """
        if not self.current_plan:
            return "No active plan."
            
        plan = self.current_plan
        
        # Count requirements by status
        req_counts = {"not_started": 0, "in_progress": 0, "completed": 0}
        for req in plan.requirements:
            req_counts[req.status] = req_counts.get(req.status, 0) + 1
            
        # Count steps by status
        step_counts = {"not_started": 0, "in_progress": 0, "completed": 0}
        for step in plan.steps:
            step_counts[step.status] = step_counts.get(step.status, 0) + 1
            
        # Calculate progress percentages
        total_reqs = len(plan.requirements)
        req_progress = (req_counts["completed"] / total_reqs * 100) if total_reqs > 0 else 0
        
        total_steps = len(plan.steps)
        step_progress = (step_counts["completed"] / total_steps * 100) if total_steps > 0 else 0
        
        # Generate the report
        report = f"# Progress Report: {plan.title}\n\n"
        report += f"## Requirements Progress: {req_progress:.1f}%\n"
        report += f"- Completed: {req_counts['completed']}/{total_reqs}\n"
        report += f"- In Progress: {req_counts['in_progress']}/{total_reqs}\n"
        report += f"- Not Started: {req_counts['not_started']}/{total_reqs}\n\n"
        
        report += f"## Steps Progress: {step_progress:.1f}%\n"
        report += f"- Completed: {step_counts['completed']}/{total_steps}\n"
        report += f"- In Progress: {step_counts['in_progress']}/{total_steps}\n"
        report += f"- Not Started: {step_counts['not_started']}/{total_steps}\n\n"
        
        report += "## Requirements\n\n"
        for req in plan.requirements:
            status_emoji = "✅" if req.status == "completed" else "🔄" if req.status == "in_progress" else "⏳"
            report += f"{status_emoji} **{req.id}**: {req.description}\n"
            if req.details:
                report += f"   - {req.details}\n"
            if req.pr_number:
                report += f"   - PR: #{req.pr_number}\n"
                
        report += "\n## Steps\n\n"
        for step in plan.steps:
            status_emoji = "✅" if step.status == "completed" else "🔄" if step.status == "in_progress" else "⏳"
            report += f"{status_emoji} **{step.id}**: {step.description}\n"
            if step.details:
                report += f"   - {step.details}\n"
            if step.pr_number:
                report += f"   - PR: #{step.pr_number}\n"
                
        return report
