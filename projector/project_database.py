import json
import os
import logging
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectDatabase:
    """Simple database for managing projects."""
    
    def __init__(self, db_path: str = "projector/projects_db.json"):
        """Initialize the project database.
        
        Args:
            db_path: Path to the JSON database file
        """
        self.db_path = db_path
        self.projects = {}
        self.load()
    
    def load(self) -> None:
        """Load projects from the database file."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    self.projects = json.load(f)
                logger.info(f"Loaded {len(self.projects)} projects from database")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse database file: {self.db_path}")
                self.projects = {}
            except Exception as e:
                logger.error(f"Error loading database: {e}")
                self.projects = {}
        else:
            logger.info(f"Database file not found. Creating new database at {self.db_path}")
            self.save()
    
    def save(self) -> None:
        """Save projects to the database file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with open(self.db_path, 'w') as f:
                json.dump(self.projects, f, indent=2)
            logger.info(f"Saved {len(self.projects)} projects to database")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            Project data or None if not found
        """
        return self.projects.get(project_id)
    
    def get_all_projects(self) -> Dict[str, Dict[str, Any]]:
        """Get all projects.
        
        Returns:
            Dictionary of all projects
        """
        return self.projects
    
    def add_project(self, project_id: str, project_data: Dict[str, Any]) -> None:
        """Add a new project or update an existing one.
        
        Args:
            project_id: ID of the project
            project_data: Project data to store
        """
        self.projects[project_id] = project_data
        self.save()
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            True if the project was deleted, False otherwise
        """
        if project_id in self.projects:
            del self.projects[project_id]
            self.save()
            return True
        return False
    
    def update_project(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """Update an existing project.
        
        Args:
            project_id: ID of the project to update
            project_data: New project data
            
        Returns:
            True if the project was updated, False if not found
        """
        if project_id in self.projects:
            self.projects[project_id] = project_data
            self.save()
            return True
        return False