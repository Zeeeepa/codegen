"""
Project class for MultiThread Slack GitHub Tool.
"""
import uuid
from datetime import datetime

class Project:
    """Represents a single project with its configuration."""
    
    def __init__(self, id, name, git_url, slack_channel=None, requirements=None, plan=None):
        """Initialize a project."""
        self.id = id
        self.name = name
        self.git_url = git_url
        self.slack_channel = slack_channel
        self.requirements = requirements or ""  # Requirements from .md files
        self.plan = plan or ""  # Implementation plan
        self.max_parallel_tasks = 3  # Default parallelism (1-10)
        self.documents = []  # List of associated documents
        self.features = {}  # Dictionary of features by name
        self.branches = {}  # Dictionary of branches by feature
        self.implementation_plan = None  # High-level plan
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.active_threads = {}  # Dictionary of active Slack threads by feature
        self.pr_status = {}  # Dictionary of PR status by feature
        self.merges = []  # List of merge events (branch merges and PR merges)
    
    def to_dict(self):
        """Convert Project object to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "git_url": self.git_url,
            "slack_channel": self.slack_channel,
            "requirements": self.requirements,
            "plan": self.plan,
            "max_parallel_tasks": self.max_parallel_tasks,
            "documents": self.documents,
            "features": self.features,
            "branches": self.branches,
            "implementation_plan": self.implementation_plan,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "active_threads": self.active_threads,
            "pr_status": self.pr_status,
            "merges": self.merges
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Project object from dictionary."""
        project = cls(
            id=data.get("id"),
            name=data.get("name"),
            git_url=data.get("git_url"),
            slack_channel=data.get("slack_channel"),
            requirements=data.get("requirements", ""),
            plan=data.get("plan", "")
        )
        
        project.max_parallel_tasks = data.get("max_parallel_tasks", 3)
        project.documents = data.get("documents", [])
        project.features = data.get("features", {})
        project.branches = data.get("branches", {})
        project.implementation_plan = data.get("implementation_plan")
        project.created_at = data.get("created_at")
        project.updated_at = data.get("updated_at")
        project.active_threads = data.get("active_threads", {})
        project.pr_status = data.get("pr_status", {})
        project.merges = data.get("merges", [])
        
        return project