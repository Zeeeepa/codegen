"""
PRD Template Structure following Base PRP Template v2
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class PRDStatus(Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    IMPLEMENTING = "implementing"
    COMPLETED = "completed"


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(Enum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    TEST = "test"


@dataclass
class DocumentationRef:
    title: str
    url: str
    why: str


@dataclass
class Task:
    id: str
    title: str
    description: str
    type: TaskType
    files: List[str]
    dependencies: List[str]
    status: TaskStatus = TaskStatus.PENDING
    agent_run_id: Optional[str] = None
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    estimated_duration: Optional[str] = None
    validation_criteria: List[str] = field(default_factory=list)


@dataclass
class IntegrationPoint:
    type: str
    description: str
    code: str


@dataclass
class PRDContext:
    documentation: List[DocumentationRef] = field(default_factory=list)
    codebase_tree: str = ""
    desired_tree: str = ""
    gotchas: List[str] = field(default_factory=list)


@dataclass
class PRDImplementation:
    data_models: str = ""
    tasks: List[Task] = field(default_factory=list)
    pseudocode: str = ""
    integration_points: List[IntegrationPoint] = field(default_factory=list)


@dataclass
class PRDValidation:
    syntax_checks: List[str] = field(default_factory=list)
    unit_tests: List[str] = field(default_factory=list)
    integration_tests: List[str] = field(default_factory=list)
    checklist: List[str] = field(default_factory=list)


@dataclass
class PRDProgress:
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    current_task: Optional[str] = None


@dataclass
class PRDTemplate:
    """
    Complete PRD Template following Base PRP Template v2 structure
    """
    id: str
    title: str
    created_at: str
    updated_at: str
    status: PRDStatus
    
    # Core PRD Content
    goal: str
    why: List[str]
    what: str
    success_criteria: List[str]
    
    # Context Information
    context: PRDContext
    
    # Implementation Details
    implementation: PRDImplementation
    
    # Validation Requirements
    validation: PRDValidation
    
    # Anti-patterns to avoid
    anti_patterns: List[str] = field(default_factory=list)
    
    # Progress tracking
    progress: PRDProgress = field(default_factory=PRDProgress)
    
    @classmethod
    def create_new(cls, title: str, goal: str, what: str) -> "PRDTemplate":
        """Create a new PRD template with basic information"""
        now = datetime.now().isoformat()
        prd_id = f"prd-{int(datetime.now().timestamp())}"
        
        return cls(
            id=prd_id,
            title=title,
            created_at=now,
            updated_at=now,
            status=PRDStatus.DRAFT,
            goal=goal,
            why=[],
            what=what,
            success_criteria=[],
            context=PRDContext(),
            implementation=PRDImplementation(),
            validation=PRDValidation(
                syntax_checks=["npm run lint", "npm run typecheck"],
                unit_tests=["npm test"],
                integration_tests=["npm run test:integration"],
                checklist=["All tests pass", "No linting errors", "Build succeeds"]
            ),
            anti_patterns=[
                "Don't skip validation because 'it should work'",
                "Don't ignore failing tests - fix them",
                "Don't use sync functions in async context",
                "Don't hardcode values that should be config",
                "Don't catch all exceptions - be specific"
            ]
        )
    
    def update_progress(self) -> None:
        """Update progress based on current task statuses"""
        if not self.implementation.tasks:
            return
            
        self.progress.total_tasks = len(self.implementation.tasks)
        self.progress.completed_tasks = sum(
            1 for task in self.implementation.tasks 
            if task.status == TaskStatus.COMPLETED
        )
        self.progress.failed_tasks = sum(
            1 for task in self.implementation.tasks 
            if task.status == TaskStatus.FAILED
        )
        
        # Find current task
        in_progress_tasks = [
            task for task in self.implementation.tasks 
            if task.status == TaskStatus.IN_PROGRESS
        ]
        self.progress.current_task = in_progress_tasks[0].id if in_progress_tasks else None
        
        self.updated_at = datetime.now().isoformat()
    
    def get_completion_percentage(self) -> float:
        """Get completion percentage"""
        if self.progress.total_tasks == 0:
            return 0.0
        return (self.progress.completed_tasks / self.progress.total_tasks) * 100
    
    def is_ready_for_implementation(self) -> bool:
        """Check if PRD is ready for implementation"""
        return (
            bool(self.goal) and
            bool(self.what) and
            len(self.success_criteria) > 0 and
            self.status in [PRDStatus.APPROVED, PRDStatus.IMPLEMENTING]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PRD to dictionary for serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "goal": self.goal,
            "why": self.why,
            "what": self.what,
            "success_criteria": self.success_criteria,
            "context": {
                "documentation": [
                    {"title": doc.title, "url": doc.url, "why": doc.why}
                    for doc in self.context.documentation
                ],
                "codebase_tree": self.context.codebase_tree,
                "desired_tree": self.context.desired_tree,
                "gotchas": self.context.gotchas
            },
            "implementation": {
                "data_models": self.implementation.data_models,
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "type": task.type.value,
                        "files": task.files,
                        "dependencies": task.dependencies,
                        "status": task.status.value,
                        "agent_run_id": task.agent_run_id,
                        "validation_results": task.validation_results,
                        "estimated_duration": task.estimated_duration,
                        "validation_criteria": task.validation_criteria
                    }
                    for task in self.implementation.tasks
                ],
                "pseudocode": self.implementation.pseudocode,
                "integration_points": [
                    {
                        "type": point.type,
                        "description": point.description,
                        "code": point.code
                    }
                    for point in self.implementation.integration_points
                ]
            },
            "validation": {
                "syntax_checks": self.validation.syntax_checks,
                "unit_tests": self.validation.unit_tests,
                "integration_tests": self.validation.integration_tests,
                "checklist": self.validation.checklist
            },
            "anti_patterns": self.anti_patterns,
            "progress": {
                "total_tasks": self.progress.total_tasks,
                "completed_tasks": self.progress.completed_tasks,
                "failed_tasks": self.progress.failed_tasks,
                "current_task": self.progress.current_task
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PRDTemplate":
        """Create PRD from dictionary"""
        # Convert context
        context_data = data.get("context", {})
        context = PRDContext(
            documentation=[
                DocumentationRef(**doc) for doc in context_data.get("documentation", [])
            ],
            codebase_tree=context_data.get("codebase_tree", ""),
            desired_tree=context_data.get("desired_tree", ""),
            gotchas=context_data.get("gotchas", [])
        )
        
        # Convert implementation
        impl_data = data.get("implementation", {})
        implementation = PRDImplementation(
            data_models=impl_data.get("data_models", ""),
            tasks=[
                Task(
                    id=task_data["id"],
                    title=task_data["title"],
                    description=task_data["description"],
                    type=TaskType(task_data["type"]),
                    files=task_data["files"],
                    dependencies=task_data["dependencies"],
                    status=TaskStatus(task_data["status"]),
                    agent_run_id=task_data.get("agent_run_id"),
                    validation_results=task_data.get("validation_results", []),
                    estimated_duration=task_data.get("estimated_duration"),
                    validation_criteria=task_data.get("validation_criteria", [])
                )
                for task_data in impl_data.get("tasks", [])
            ],
            pseudocode=impl_data.get("pseudocode", ""),
            integration_points=[
                IntegrationPoint(**point) for point in impl_data.get("integration_points", [])
            ]
        )
        
        # Convert validation
        val_data = data.get("validation", {})
        validation = PRDValidation(
            syntax_checks=val_data.get("syntax_checks", []),
            unit_tests=val_data.get("unit_tests", []),
            integration_tests=val_data.get("integration_tests", []),
            checklist=val_data.get("checklist", [])
        )
        
        # Convert progress
        prog_data = data.get("progress", {})
        progress = PRDProgress(
            total_tasks=prog_data.get("total_tasks", 0),
            completed_tasks=prog_data.get("completed_tasks", 0),
            failed_tasks=prog_data.get("failed_tasks", 0),
            current_task=prog_data.get("current_task")
        )
        
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            status=PRDStatus(data["status"]),
            goal=data["goal"],
            why=data["why"],
            what=data["what"],
            success_criteria=data["success_criteria"],
            context=context,
            implementation=implementation,
            validation=validation,
            anti_patterns=data.get("anti_patterns", []),
            progress=progress
        )

