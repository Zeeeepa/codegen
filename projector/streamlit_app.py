import streamlit as st
import uuid
import json
import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from project_database import ProjectDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = ProjectDatabase()

# Initialize session state
if "active_project" not in st.session_state:
    st.session_state.active_project = None
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}

class Project:
    """Project class for managing project data and operations."""
    
    def __init__(self, name: str, github_url: str = "", slack_channel: str = "", concurrency: int = 1):
        """Initialize a project.
        
        Args:
            name: Name of the project
            github_url: GitHub repository URL
            slack_channel: Slack channel ID
            concurrency: Number of concurrent feature lifecycles (1-10)
        """
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
        """Convert project to dictionary for storage.
        
        Returns:
            Dictionary representation of the project
        """
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
        """Create a project from a dictionary.
        
        Args:
            data: Dictionary representation of the project
            
        Returns:
            Project instance
        """
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
        """Initialize the project by processing documents and generating structures."""
        if not self.documents:
            return
        
        # Simulate document processing with LLM
        with st.spinner(f"Initializing project '{self.name}'..."):
            time.sleep(2)  # Simulate processing time
            
            # Generate sample tree structure
            self.tree_structure = {
                "name": self.name,
                "progress": 65,
                "children": [
                    {
                        "name": "User Authentication",
                        "progress": 100,
                        "completed": True,
                        "children": [
                            {"name": "Database Schema", "progress": 100, "completed": True},
                            {"name": "Basic Auth Endpoints", "progress": 100, "completed": True},
                            {"name": "Social Login", "progress": 100, "completed": True},
                            {"name": "Password Reset", "progress": 100, "completed": True},
                            {"name": "Two-Factor Auth", "progress": 0, "completed": False}
                        ]
                    },
                    {
                        "name": "Product Catalog",
                        "progress": 75,
                        "completed": False,
                        "children": [
                            {"name": "Database Schema", "progress": 100, "completed": True},
                            {"name": "Basic CRUD API", "progress": 100, "completed": True},
                            {"name": "Search Functionality", "progress": 100, "completed": True},
                            {"name": "Filtering Options", "progress": 0, "completed": False},
                            {"name": "Sorting Options", "progress": 0, "completed": False}
                        ]
                    },
                    {
                        "name": "Shopping Cart",
                        "progress": 50,
                        "completed": False,
                        "children": [
                            {"name": "Database Schema", "progress": 100, "completed": True},
                            {"name": "Add/Remove Items", "progress": 100, "completed": True},
                            {"name": "Update Quantities", "progress": 0, "completed": False},
                            {"name": "Save for Later", "progress": 0, "completed": False},
                            {"name": "Cart Recovery", "progress": 0, "completed": False}
                        ]
                    },
                    {
                        "name": "Checkout Process",
                        "progress": 0,
                        "completed": False,
                        "children": [
                            {"name": "Payment Integration", "progress": 0, "completed": False},
                            {"name": "Order Confirmation", "progress": 0, "completed": False},
                            {"name": "Email Notifications", "progress": 0, "completed": False},
                            {"name": "Order History", "progress": 0, "completed": False}
                        ]
                    }
                ]
            }
            
            # Generate sample step-by-step list
            self.step_by_step = [
                "1. Set up project repository and basic structure",
                "2. Implement user authentication system",
                "3. Design and implement database schema",
                "4. Create product catalog with search functionality",
                "5. Implement shopping cart functionality",
                "6. Develop checkout process with payment integration",
                "7. Add email notification system",
                "8. Implement user dashboard and order history",
                "9. Add advanced features (wishlists, reviews, etc.)",
                "10. Perform testing and optimization"
            ]
            
            self.initialized = True
            
            # Save the project
            save_project(self)

def load_projects() -> None:
    """Load projects from the database."""
    projects_data = db.get_all_projects()
    st.session_state.projects = {
        project_id: Project.from_dict(project_data)
        for project_id, project_data in projects_data.items()
    }

def save_project(project: Project) -> None:
    """Save a project to the database.
    
    Args:
        project: Project to save
    """
    st.session_state.projects[project.id] = project
    db.add_project(project.id, project.to_dict())

def delete_project(project_id: str) -> None:
    """Delete a project.
    
    Args:
        project_id: ID of the project to delete
    """
    if project_id in st.session_state.projects:
        del st.session_state.projects[project_id]
        db.delete_project(project_id)
        if st.session_state.active_project == project_id:
            st.session_state.active_project = None

def render_tree_structure(node: Dict[str, Any], indent: int = 0) -> None:
    """Render a tree structure node.
    
    Args:
        node: Tree structure node
        indent: Indentation level
    """
    if "name" not in node:
        return
    
    # Render the node
    progress = node.get("progress", 0)
    completed = node.get("completed", False)
    
    # Create indentation
    prefix = ""
    if indent > 0:
        prefix = "│   " * (indent - 1) + "├── "
    
    # Render the node with progress
    if "children" in node and node["children"]:
        st.markdown(f"{prefix}**{node['name']}** [{progress}%]")
    else:
        checkbox = "✓" if completed else " "
        st.markdown(f"{prefix}{node['name']} [{checkbox}]")
    
    # Render children
    if "children" in node:
        for child in node["children"]:
            render_tree_structure(child, indent + 1)

def render_step_by_step(steps: List[str]) -> None:
    """Render a step-by-step list.
    
    Args:
        steps: List of steps
    """
    for step in steps:
        st.markdown(f"- {step}")

def render_chat_interface(project_id: str) -> None:
    """Render the chat interface for a project.
    
    Args:
        project_id: ID of the project
    """
    if project_id not in st.session_state.chat_history:
        st.session_state.chat_history[project_id] = []
    
    # Display chat history
    for message in st.session_state.chat_history[project_id]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type a message..."):
        # Add user message to chat history
        st.session_state.chat_history[project_id].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simulate assistant response
        with st.chat_message("assistant"):
            response = f"I'm processing your request about '{prompt}'. This is a simulated response for the project chat interface."
            st.markdown(response)
        
        # Add assistant message to chat history
        st.session_state.chat_history[project_id].append({"role": "assistant", "content": response})

def create_project_form() -> None:
    """Render the create project form."""
    with st.form("create_project_form"):
        st.subheader("Create New Project")
        name = st.text_input("Project Name")
        github_url = st.text_input("GitHub URL (optional)")
        slack_channel = st.text_input("Slack Channel ID (optional)")
        concurrency = st.slider("Concurrency", min_value=1, max_value=10, value=2, 
                               help="Number of concurrent feature lifecycles")
        
        submitted = st.form_submit_button("Create Project")
        if submitted and name:
            project = Project(name=name, github_url=github_url, 
                             slack_channel=slack_channel, concurrency=concurrency)
            save_project(project)
            st.session_state.active_project = project.id
            st.success(f"Project '{name}' created successfully!")
            st.rerun()

def project_settings_form(project: Project) -> None:
    """Render the project settings form.
    
    Args:
        project: Project to edit
    """
    with st.form(f"project_settings_form_{project.id}"):
        st.subheader(f"Settings for {project.name}")
        name = st.text_input("Project Name", value=project.name)
        github_url = st.text_input("GitHub URL", value=project.github_url)
        slack_channel = st.text_input("Slack Channel ID", value=project.slack_channel)
        concurrency = st.slider("Concurrency", min_value=1, max_value=10, value=project.concurrency, 
                               help="Number of concurrent feature lifecycles")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Save Settings")
        with col2:
            delete = st.form_submit_button("Delete Project", type="secondary")
        
        if submitted:
            project.name = name
            project.github_url = github_url
            project.slack_channel = slack_channel
            project.concurrency = concurrency
            save_project(project)
            st.success(f"Settings for '{name}' updated successfully!")
            st.rerun()
        
        if delete:
            delete_project(project.id)
            st.success(f"Project '{project.name}' deleted successfully!")
            st.rerun()

def document_upload_form(project: Project) -> None:
    """Render the document upload form.
    
    Args:
        project: Project to upload documents to
    """
    with st.form(f"document_upload_form_{project.id}"):
        st.subheader("Upload Documents")
        uploaded_file = st.file_uploader("Upload a document", type=["txt", "pdf", "docx", "md"])
        document_text = st.text_area("Or paste document content here")
        
        submitted = st.form_submit_button("Add Document")
        if submitted and (uploaded_file or document_text):
            if uploaded_file:
                # In a real application, we would process the file
                document_name = uploaded_file.name
                document_content = "Sample content from uploaded file"
            else:
                document_name = f"Document {len(project.documents) + 1}"
                document_content = document_text
            
            project.documents.append({
                "name": document_name,
                "content": document_content,
                "timestamp": time.time()
            })
            
            save_project(project)
            st.success(f"Document '{document_name}' added successfully!")
            st.rerun()

def render_project_tab(project: Project) -> None:
    """Render a project tab.
    
    Args:
        project: Project to render
    """
    # Project header with settings and concurrency
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader(project.name)
    with col2:
        st.number_input("Concurrency", min_value=1, max_value=10, value=project.concurrency, 
                       key=f"concurrency_{project.id}", on_change=lambda: update_concurrency(project))
    with col3:
        if st.button("Project Settings", key=f"settings_btn_{project.id}"):
            project_settings_form(project)
    
    # Document upload and initialization
    if not project.initialized:
        document_upload_form(project)
        if project.documents:
            if st.button("Initialize Project", key=f"init_btn_{project.id}"):
                project.initialize()
                st.rerun()
    
    # Display project content if initialized
    if project.initialized:
        # Create three columns for the layout
        col1, col2, col3 = st.columns([1, 2, 1])
        
        # Left column: Step-by-step structure
        with col1:
            st.markdown("### Step by Step Structure")
            render_step_by_step(project.step_by_step)
        
        # Middle column: Project's context document view
        with col2:
            st.markdown("### Project Context")
            if project.documents:
                tabs = st.tabs([doc["name"] for doc in project.documents])
                for i, tab in enumerate(tabs):
                    with tab:
                        st.markdown(project.documents[i]["content"])
            else:
                st.info("No documents added to this project yet.")
        
        # Right column: Tree structure view
        with col3:
            st.markdown("### Implementation Progress")
            render_tree_structure(project.tree_structure)

def update_concurrency(project: Project) -> None:
    """Update the concurrency setting for a project.
    
    Args:
        project: Project to update
    """
    concurrency_key = f"concurrency_{project.id}"
    if concurrency_key in st.session_state:
        project.concurrency = st.session_state[concurrency_key]
        save_project(project)

def main():
    """Main function to render the Streamlit app."""
    # Set page config
    st.set_page_config(
        page_title="Projector",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Load projects
    load_projects()
    
    # Header
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.button("Settings")
    with col2:
        st.button("Dashboard")
    with col3:
        if st.button("Add Project +"):
            create_project_form()
    
    # Main content
    if not st.session_state.projects:
        st.info("No projects yet. Click 'Add Project +' to create one.")
        create_project_form()
    else:
        # Create tabs for projects
        project_ids = list(st.session_state.projects.keys())
        project_names = [st.session_state.projects[pid].name for pid in project_ids]
        
        # Add a "+" tab for creating a new project
        tabs = st.tabs(project_names)
        
        # Render each project tab
        for i, tab in enumerate(tabs):
            with tab:
                project_id = project_ids[i]
                project = st.session_state.projects[project_id]
                st.session_state.active_project = project_id
                render_project_tab(project)
        
        # Chat interface at the bottom
        st.markdown("---")
        st.markdown("### Chat Interface")
        if st.session_state.active_project:
            render_chat_interface(st.session_state.active_project)
        else:
            st.info("Select a project to use the chat interface.")

if __name__ == "__main__":
    main()