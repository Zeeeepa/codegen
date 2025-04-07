"""
Database for project persistence.
"""
import os
import json
import logging
from datetime import datetime
import uuid

class Project:
    """Represents a single project with its configuration."""
    
    def __init__(self, project_id, name, git_url, slack_channel=None):
        """Initialize a project."""
        self.id = project_id or str(uuid.uuid4())
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


class ProjectDatabase:
    """Database for project persistence."""
    
    def __init__(self, db_file="projects_db.json"):
        """Initialize the database."""
        self.db_file = db_file
        self.logger = logging.getLogger(__name__)
        
        # Create database file if it doesn't exist
        if not os.path.exists(db_file):
            self._init_database()
    
    def _init_database(self):
        """Initialize an empty database."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump({"projects": {}}, f)
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
    
    def _read_database(self):
        """Read the database file."""
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading database: {e}")
            return {"projects": {}}
    
    def _write_database(self, data):
        """Write data to the database file."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error writing to database: {e}")
            return False
    
    def save_project(self, project):
        """Save a project to the database."""
        db_data = self._read_database()
        
        # Update the project's updated_at timestamp
        project.updated_at = datetime.now().isoformat()
        
        # Add or update project
        db_data["projects"][project.id] = project.to_dict()
        
        return self._write_database(db_data)
    
    def get_project(self, project_id):
        """Get a project by ID."""
        db_data = self._read_database()
        project_data = db_data["projects"].get(project_id)
        
        if project_data:
            return Project.from_dict(project_data)
        
        return None
    
    def list_projects(self):
        """List all projects."""
        db_data = self._read_database()
        
        projects = []
        for project_data in db_data["projects"].values():
            projects.append(Project.from_dict(project_data))
        
        return projects
    
    def delete_project(self, project_id):
        """Delete a project."""
        db_data = self._read_database()
        
        if project_id in db_data["projects"]:
            del db_data["projects"][project_id]
            return self._write_database(db_data)
        
        return False
    
    def update_project_plan(self, project_id, plan):
        """Update a project's implementation plan."""
        project = self.get_project(project_id)
        
        if project:
            project.implementation_plan = plan
            return self.save_project(project)
        
        return False
    
    def add_document_to_project(self, project_id, document_path):
        """Add a document to a project."""
        project = self.get_project(project_id)
        
        if project:
            if document_path not in project.documents:
                project.documents.append(document_path)
                return self.save_project(project)
            return True
        
        return False
    
    def update_project_features(self, project_id, features):
        """Update a project's features."""
        project = self.get_project(project_id)
        
        if project:
            project.features = features
            return self.save_project(project)
        
        return False
    
    def create_project(self, name, git_url, slack_channel=None):
        """Create a new project."""
        project = Project(None, name, git_url, slack_channel)
        return self.save_project(project) and project.id
