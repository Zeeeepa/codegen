import streamlit as st
import uuid
import json
import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database class for managing projects
class ProjectDatabase:
    """Simple database for managing projects."""
    
    def __init__(self, db_path: str = "projector/projects_db.json"):
        """Initialize the project database."""
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
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, 'w') as f:
                json.dump(self.projects, f, indent=2)
            logger.info(f"Saved {len(self.projects)} projects to database")
        except Exception as e:
            logger.error(f"Error saving database: {e}")
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def get_all_projects(self) -> Dict[str, Dict[str, Any]]:
        """Get all projects."""
        return self.projects
    
    def add_project(self, project_id: str, project_data: Dict[str, Any]) -> None:
        """Add a new project or update an existing one."""
        self.projects[project_id] = project_data
        self.save()
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if project_id in self.projects:
            del self.projects[project_id]
            self.save()
            return True
        return False
    
    def update_project(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """Update an existing project."""
        if project_id in self.projects:
            self.projects[project_id] = project_data
            self.save()
            return True
        return False

# Project class for managing project data
class Project:
    """Project class for managing project data and operations."""
    
    def __init__(self, name: str, github_url: str = "", slack_channel: str = "", concurrency: int = 1):
        """Initialize a project."""
        self.id = str(uuid.uuid4())
        self.name = name
        self.github_url = github_url
        self.slack_channel = slack_channel
        self.concurrency = max(1, min(10, concurrency))  # Ensure concurrency is between 1 and 10
        self.documents = []
        self.tree_structure = {}
        self.step_by_step = []
        self.initialized = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "github_url": self.github_url,
            "slack_channel": self.slack_channel,
            "concurrency": self.concurrency,
            "documents": self.documents,
            "tree_structure": self.tree_structure,
            "step_by_step": self.step_by_step,
            "initialized": self.initialized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create a project from dictionary data."""
        project = cls(
            name=data["name"],
            github_url=data.get("github_url", ""),
            slack_channel=data.get("slack_channel", ""),
            concurrency=data.get("concurrency", 1)
        )
        project.id = data["id"]
        project.documents = data.get("documents", [])
        project.tree_structure = data.get("tree_structure", {})
        project.step_by_step = data.get("step_by_step", [])
        project.initialized = data.get("initialized", False)
        return project
    
    def initialize(self) -> None:
        """Initialize the project by processing documents with LLM."""
        # Simulate LLM processing
        time.sleep(1)  # Simulate processing time
        
        # Generate step-by-step structure
        self.step_by_step = [
            {"name": "Requirements Analysis", "status": "completed"},
            {"name": "System Design", "status": "completed"},
            {"name": "Implementation", "status": "in_progress"},
            {"name": "Testing", "status": "not_started"},
            {"name": "Deployment", "status": "not_started"}
        ]
        
        # Generate tree structure
        self.tree_structure = {
            "name": self.name,
            "progress": 65,
            "children": [
                {
                    "name": "User Authentication",
                    "progress": 100,
                    "status": "completed",
                    "children": [
                        {"name": "Database Schema", "status": "completed"},
                        {"name": "Basic Auth Endpoints", "status": "completed"},
                        {"name": "Social Login", "status": "completed"},
                        {"name": "Password Reset", "status": "completed"},
                        {"name": "Two-Factor Auth", "status": "not_started"}
                    ]
                },
                {
                    "name": "Product Catalog",
                    "progress": 75,
                    "status": "in_progress",
                    "children": [
                        {"name": "Database Schema", "status": "completed"},
                        {"name": "Basic CRUD API", "status": "completed"},
                        {"name": "Search Functionality", "status": "completed"},
                        {"name": "Filtering Options", "status": "not_started"},
                        {"name": "Sorting Options", "status": "not_started"}
                    ]
                },
                {
                    "name": "Shopping Cart",
                    "progress": 50,
                    "status": "in_progress",
                    "children": [
                        {"name": "Database Schema", "status": "completed"},
                        {"name": "Add/Remove Items", "status": "completed"},
                        {"name": "Update Quantities", "status": "not_started"},
                        {"name": "Save for Later", "status": "not_started"},
                        {"name": "Cart Recovery", "status": "not_started"}
                    ]
                },
                {
                    "name": "Checkout Process",
                    "progress": 0,
                    "status": "not_started",
                    "children": [
                        {"name": "Payment Integration", "status": "not_started"},
                        {"name": "Order Confirmation", "status": "not_started"},
                        {"name": "Email Notifications", "status": "not_started"},
                        {"name": "Order History", "status": "not_started"}
                    ]
                }
            ]
        }
        
        self.initialized = True

# Initialize database
db = ProjectDatabase()

# Initialize session state
if "active_project" not in st.session_state:
    st.session_state.active_project = None
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if "open_tabs" not in st.session_state:
    st.session_state.open_tabs = []

# Load projects from database
for project_id, project_data in db.get_all_projects().items():
    st.session_state.projects[project_id] = Project.from_dict(project_data)
    if project_id not in st.session_state.open_tabs:
        st.session_state.open_tabs.append(project_id)

# Callback functions
def add_project():
    """Add a new project."""
    project_name = st.session_state.new_project_name
    if project_name:
        project = Project(name=project_name)
        st.session_state.projects[project.id] = project
        st.session_state.active_project = project.id
        if project.id not in st.session_state.open_tabs:
            st.session_state.open_tabs.append(project.id)
        db.add_project(project.id, project.to_dict())
        st.session_state.new_project_name = ""

def close_tab(project_id):
    """Close a project tab."""
    if project_id in st.session_state.open_tabs:
        st.session_state.open_tabs.remove(project_id)
    if st.session_state.active_project == project_id:
        st.session_state.active_project = st.session_state.open_tabs[0] if st.session_state.open_tabs else None

def update_project_settings(project_id):
    """Update project settings."""
    project = st.session_state.projects[project_id]
    project.github_url = st.session_state[f"github_url_{project_id}"]
    project.slack_channel = st.session_state[f"slack_channel_{project_id}"]
    project.concurrency = max(1, min(10, st.session_state[f"concurrency_{project_id}"]))
    db.update_project(project_id, project.to_dict())

def initialize_project(project_id):
    """Initialize a project."""
    project = st.session_state.projects[project_id]
    project.initialize()
    db.update_project(project_id, project.to_dict())

def send_message(project_id):
    """Send a chat message."""
    message = st.session_state[f"chat_input_{project_id}"]
    if message:
        if project_id not in st.session_state.chat_history:
            st.session_state.chat_history[project_id] = []
        
        # Add user message
        st.session_state.chat_history[project_id].append({"role": "user", "content": message})
        
        # Simulate AI response
        ai_response = f"I'll help you with your project '{st.session_state.projects[project_id].name}'. What specific aspect would you like to discuss?"
        st.session_state.chat_history[project_id].append({"role": "assistant", "content": ai_response})
        
        # Clear input
        st.session_state[f"chat_input_{project_id}"] = ""

def upload_document(project_id):
    """Upload a document to a project."""
    if st.session_state[f"document_upload_{project_id}"] is not None:
        uploaded_file = st.session_state[f"document_upload_{project_id}"]
        
        # Read file content
        content = uploaded_file.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        
        # Add document to project
        project = st.session_state.projects[project_id]
        project.documents.append({
            "name": uploaded_file.name,
            "content": content,
            "type": uploaded_file.type
        })
        
        # Update project in database
        db.update_project(project_id, project.to_dict())

# Main app layout
def main():
    # Header
    st.title("Projector - Project Management System")
    
    # Top navigation
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.button("Settings", key="settings_button")
    with col2:
        st.button("Dashboard", key="dashboard_button")
    with col3:
        st.text_input("New Project Name", key="new_project_name")
        st.button("Add Project", key="add_project_button", on_click=add_project)
    
    # Main content area with three columns
    left_col, middle_col, right_col = st.columns([1, 2, 1])
    
    # Left column - Step by Step Structure
    with left_col:
        st.subheader("Step by Step Structure")
        if st.session_state.active_project and st.session_state.active_project in st.session_state.projects:
            project = st.session_state.projects[st.session_state.active_project]
            if project.initialized:
                for step in project.step_by_step:
                    status_icon = "✅" if step["status"] == "completed" else "🔄" if step["status"] == "in_progress" else "⏳"
                    st.write(f"{status_icon} {step['name']}")
            else:
                st.info("Initialize the project to generate step-by-step structure.")
        else:
            st.info("Select a project to view its step-by-step structure.")
    
    # Middle column - Project Tabs and Content
    with middle_col:
        # Project tabs
        if st.session_state.open_tabs:
            tabs = []
            for project_id in st.session_state.open_tabs:
                if project_id in st.session_state.projects:
                    project = st.session_state.projects[project_id]
                    tabs.append(project.name)
                else:
                    st.session_state.open_tabs.remove(project_id)
            
            tab_index = 0
            if st.session_state.active_project in st.session_state.open_tabs:
                tab_index = st.session_state.open_tabs.index(st.session_state.active_project)
            
            selected_tab = st.tabs(tabs)
            for i, tab in enumerate(selected_tab):
                with tab:
                    if i < len(st.session_state.open_tabs):
                        project_id = st.session_state.open_tabs[i]
                        st.session_state.active_project = project_id
                        project = st.session_state.projects[project_id]
                        
                        # Project settings and controls
                        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                        with col1:
                            st.number_input("Concurrency", min_value=1, max_value=10, value=project.concurrency, key=f"concurrency_{project_id}")
                        with col2:
                            st.button("Project Settings", key=f"settings_{project_id}")
                        with col3:
                            st.button("Initialize", key=f"initialize_{project_id}", on_click=initialize_project, args=(project_id,))
                        with col4:
                            st.button("Close Tab", key=f"close_{project_id}", on_click=close_tab, args=(project_id,))
                        
                        # Project settings form
                        with st.expander("Project Settings"):
                            st.text_input("GitHub URL", value=project.github_url, key=f"github_url_{project_id}")
                            st.text_input("Slack Channel ID", value=project.slack_channel, key=f"slack_channel_{project_id}")
                            st.button("Save Settings", key=f"save_settings_{project_id}", on_click=update_project_settings, args=(project_id,))
                        
                        # Document upload
                        with st.expander("Upload Documents"):
                            st.file_uploader("Upload Document", key=f"document_upload_{project_id}", on_change=upload_document, args=(project_id,))
                            
                            # Display uploaded documents
                            if project.documents:
                                st.subheader("Uploaded Documents")
                                for doc in project.documents:
                                    st.write(f"📄 {doc['name']}")
                                    with st.expander(f"View {doc['name']}"):
                                        st.text(doc['content'][:1000] + "..." if len(doc['content']) > 1000 else doc['content'])
                        
                        # Project content
                        if project.initialized:
                            st.subheader("Project Content")
                            st.write("Project has been initialized with LLM processing.")
                        else:
                            st.info("Click 'Initialize' to process project documents with LLM.")
        else:
            st.info("Add a project to get started.")
    
    # Right column - Tree Structure View
    with right_col:
        st.subheader("Tree Structure View")
        if st.session_state.active_project and st.session_state.active_project in st.session_state.projects:
            project = st.session_state.projects[st.session_state.active_project]
            if project.initialized and project.tree_structure:
                # Display tree structure
                st.write(f"{project.tree_structure['name']} [{project.tree_structure['progress']}%]")
                
                for module in project.tree_structure.get("children", []):
                    status_icon = "✅" if module.get("status") == "completed" else "🔄" if module.get("status") == "in_progress" else "⏳"
                    st.write(f"├── {module['name']} {status_icon} [{module.get('progress', 0)}%]")
                    
                    for item in module.get("children", []):
                        status_icon = "✅" if item.get("status") == "completed" else "🔄" if item.get("status") == "in_progress" else "⏳"
                        st.write(f"│   ├── {item['name']} {status_icon}")
            else:
                st.info("Initialize the project to generate tree structure.")
        else:
            st.info("Select a project to view its tree structure.")
    
    # Chat interface at the bottom
    st.subheader("Chat Interface")
    if st.session_state.active_project and st.session_state.active_project in st.session_state.projects:
        project_id = st.session_state.active_project
        
        # Display chat history
        if project_id in st.session_state.chat_history:
            for message in st.session_state.chat_history[project_id]:
                if message["role"] == "user":
                    st.write(f"👤 **You**: {message['content']}")
                else:
                    st.write(f"🤖 **Assistant**: {message['content']}")
        
        # Chat input
        st.text_input("Type your message...", key=f"chat_input_{project_id}", on_change=send_message, args=(project_id,))
    else:
        st.info("Select a project to start chatting.")

if __name__ == "__main__":
    main()