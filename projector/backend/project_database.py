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
        
        # Set additional properties
        project.max_parallel_tasks = data.get("max_parallel_tasks", 2)
        project.documents = data.get("documents", [])
        project.features = data.get("features", {})
        project.implementation_plan = data.get("implementation_plan")
        project.created_at = data.get("created_at", project.created_at)
        project.updated_at = data.get("updated_at", project.updated_at)
        
        return project

class ProjectDatabase:
    """Database for project persistence."""
    
    def __init__(self, db_file="projects_db.json"):
        """Initialize the project database."""
        self.logger = logging.getLogger(__name__)
        self.db_file = db_file
        self.projects = {}
        
        # Initialize the database
        self._init_database()
    
    def _init_database(self):
        """Initialize the database if it doesn't exist."""
        if not os.path.exists(self.db_file):
            self._write_database({})
        else:
            self._read_database()
    
    def _read_database(self):
        """Read the database from disk."""
        try:
            with open(self.db_file, 'r') as f:
                data = json.load(f)
                self.projects = {
                    project_id: Project.from_dict(project_data)
                    for project_id, project_data in data.items()
                }
        except Exception as e:
            self.logger.error(f"Error reading database: {e}")
            self.projects = {}
    
    def _write_database(self, data):
        """Write the database to disk."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error writing database: {e}")
    
    def save_project(self, project):
        """Save a project to the database."""
        try:
            # Update the project's updated_at timestamp
            project.updated_at = datetime.now().isoformat()
            
            # Read the current database
            with open(self.db_file, 'r') as f:
                data = json.load(f)
            
            # Update the project data
            data[project.id] = project.to_dict()
            
            # Write the updated database
            self._write_database(data)
            
            # Update the in-memory projects
            self.projects[project.id] = project
            
            return True
        except Exception as e:
            self.logger.error(f"Error saving project: {e}")
            return False
    
    def get_project(self, project_id):
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def list_projects(self):
        """List all projects."""
        return list(self.projects.values())
    
    def get_all_projects(self):
        """Get all projects as a list.
        
        This is an alias for list_projects() for better readability.
        """
        return self.list_projects()
    
    def delete_project(self, project_id):
        """Delete a project by ID."""
        try:
            # Read the current database
            with open(self.db_file, 'r') as f:
                data = json.load(f)
            
            # Remove the project
            if project_id in data:
                del data[project_id]
                
                # Write the updated database
                self._write_database(data)
                
                # Update the in-memory projects
                if project_id in self.projects:
                    del self.projects[project_id]
                
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting project: {e}")
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
            return True  # Document already exists
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
        # Create a new project
        project = Project(
            project_id=None,  # Will be auto-generated
            name=name,
            git_url=git_url,
            slack_channel=slack_channel
        )
        
        # Save the project
        if self.save_project(project):
            return project.id
        return None
