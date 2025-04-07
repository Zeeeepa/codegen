"""
Project class for MultiThread Slack GitHub Tool.
"""
import uuid
from datetime import datetime

class Project:
    """Represents a single project with its configuration."""
    
    def __init__(self, project_id, name, git_url, slack_channel=None):
        """Initialize a project."""
        self.id = project_id
        self.name = name
        self.git_url = git_url
        self.slack_channel = slack_channel
        self.max_parallel_tasks = 2  # Default parallelism (1-10)
        self.documents = []  # List of associated documents
        self.features = {}  # Dictionary of features by name
        self.implementation_plan = None  # High-level plan
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def to_dict(self):
        """Convert Project object to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "git_url": self.git_url,
            "slack_channel": self.slack_channel,
            "max_parallel_tasks": self.max_parallel_tasks,
            "documents": self.documents,
            "features": self.features,
            "implementation_plan": self.implementation_plan,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Project object from dictionary."""
        project = cls(
            project_id=data.get("id"),
            name=data.get("name"),
            git_url=data.get("git_url"),
            slack_channel=data.get("slack_channel")
        )
        
        project.max_parallel_tasks = data.get("max_parallel_tasks", 2)
        project.documents = data.get("documents", [])
        project.features = data.get("features", {})
        project.implementation_plan = data.get("implementation_plan")
        project.created_at = data.get("created_at")
        project.updated_at = data.get("updated_at")
        
        return project