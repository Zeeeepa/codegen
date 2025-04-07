"""
Streamlit application for the Projector system.
This is a simplified version that combines all functionality in a single file.
"""
import streamlit as st
import os
import sys
import logging
import json
import time
from datetime import datetime
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("projector/app.log"),
        logging.StreamHandler()
    ]
)

# Set page config
st.set_page_config(
    page_title="Projector - Project Management",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Project class for data structure
class Project:
    """Project data structure."""
    
    def __init__(self, project_id=None, name=None, git_url=None, slack_channel=None):
        """Initialize a project."""
        self.id = project_id or str(uuid.uuid4())
        self.name = name
        self.git_url = git_url
        self.slack_channel = slack_channel
        self.max_parallel_tasks = 2
        self.documents = []
        self.features = {}
        self.implementation_plan = None
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert the project to a dictionary."""
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
        """Create a project from a dictionary."""
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

# Project database for persistence
class ProjectDatabase:
    """Database for project persistence."""
    
    def __init__(self, db_file="projector/projects_db.json"):
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
        """Get all projects as a list."""
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

# Initialize session state
def initialize_session_state():
    """Initialize the session state."""
    if "selected_project" not in st.session_state:
        st.session_state.selected_project = None
    
    if "show_create_project" not in st.session_state:
        st.session_state.show_create_project = False
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}

# Render the create project form
def render_create_project_form():
    """Render the form to create a new project."""
    st.subheader("Create New Project")
    
    # Project name
    name = st.text_input("Project Name", key="new_project_name")
    
    # GitHub URL
    git_url = st.text_input("GitHub Repository URL", key="new_project_git_url")
    
    # Slack channel
    slack_channel = st.text_input("Slack Channel ID (optional)", key="new_project_slack_channel")
    
    # Create button
    if st.button("Create Project", key="create_project_button"):
        if not name:
            st.error("Project name is required.")
            return
        
        if not git_url:
            st.error("GitHub repository URL is required.")
            return
        
        # Create the project
        project_database = ProjectDatabase()
        project_id = project_database.create_project(name, git_url, slack_channel)
        
        if project_id:
            st.success(f"Project '{name}' created successfully!")
            st.session_state.selected_project = project_id
            st.session_state.show_create_project = False
            st.experimental_rerun()
        else:
            st.error("Failed to create project.")

# Render the tabbed interface for projects
def render_tabbed_interface(projects):
    """Render a tabbed interface for projects with closable tabs."""
    if not projects:
        st.info("No projects found. Create a new project to get started.")
        return
    
    # Get the currently selected project ID
    selected_project_id = st.session_state.get("selected_project")
    
    # Create a list of project names for tabs
    project_names = [f"{project.name}|[X]" for project in projects]
    
    # Create tabs
    tabs = st.tabs(project_names)
    
    # Render content for each tab
    for i, tab in enumerate(tabs):
        with tab:
            project = projects[i]
            
            # Set the selected project when a tab is clicked
            if selected_project_id != project.id:
                st.session_state.selected_project = project.id
            
            # Render project content
            st.subheader(f"Project: {project.name}")
            
            # Project context document view
            st.write("Project's context document view")
            
            # Display documents if available
            if project.documents:
                for doc in project.documents:
                    st.write(f"- {os.path.basename(doc)}")
            else:
                st.info("No documents uploaded yet. Upload documents to get started.")
            
            # Concurrency setting
            col1, col2 = st.columns([3, 1])
            
            with col1:
                concurrency = st.number_input(
                    "Concurrency",
                    min_value=1,
                    max_value=10,
                    value=project.max_parallel_tasks,
                    help="Set the maximum number of concurrent feature lifecycles"
                )
                
                if concurrency != project.max_parallel_tasks:
                    project.max_parallel_tasks = concurrency
                    project_database = ProjectDatabase()
                    project_database.save_project(project)
            
            with col2:
                if st.button("Project Settings", key=f"settings_{project.id}"):
                    st.session_state[f"show_settings_{project.id}"] = True
            
            # Project settings dialog
            if st.session_state.get(f"show_settings_{project.id}", False):
                with st.expander("Project Settings", expanded=True):
                    # GitHub URL
                    github_url = st.text_input(
                        "GitHub Repository URL",
                        value=project.git_url,
                        key=f"github_url_{project.id}"
                    )
                    
                    # Slack channel
                    slack_channel = st.text_input(
                        "Slack Channel ID (optional)",
                        value=project.slack_channel or "",
                        key=f"slack_channel_{project.id}"
                    )
                    
                    # Save settings
                    if st.button("Save", key=f"save_settings_{project.id}"):
                        project.git_url = github_url
                        project.slack_channel = slack_channel
                        
                        project_database = ProjectDatabase()
                        if project_database.save_project(project):
                            st.success("Settings saved successfully!")
                            st.session_state[f"show_settings_{project.id}"] = False
                            st.experimental_rerun()
                        else:
                            st.error("Failed to save settings.")
                    
                    # Cancel button
                    if st.button("Cancel", key=f"cancel_settings_{project.id}"):
                        st.session_state[f"show_settings_{project.id}"] = False
                        st.experimental_rerun()
            
            # Initialize project button
            if st.button("Initialize", key=f"initialize_{project.id}"):
                st.session_state[f"initializing_{project.id}"] = True
                st.info("Initializing project... This may take a few moments.")
                
                # Simulate initialization with a delay
                time.sleep(2)
                
                # Create a sample implementation plan
                project.implementation_plan = {
                    "tasks": [
                        {
                            "id": "task1",
                            "title": "Setup project structure",
                            "description": "Create the basic project structure and configuration files",
                            "status": "completed",
                            "subtasks": []
                        },
                        {
                            "id": "task2",
                            "title": "Implement core functionality",
                            "description": "Implement the core functionality of the project",
                            "status": "in_progress",
                            "subtasks": [
                                {
                                    "id": "subtask1",
                                    "title": "Create data models",
                                    "status": "completed"
                                },
                                {
                                    "id": "subtask2",
                                    "title": "Implement business logic",
                                    "status": "in_progress"
                                }
                            ]
                        },
                        {
                            "id": "task3",
                            "title": "Create user interface",
                            "description": "Design and implement the user interface",
                            "status": "not_started",
                            "subtasks": []
                        }
                    ]
                }
                
                # Save the project with the implementation plan
                project_database = ProjectDatabase()
                project_database.save_project(project)
                
                st.success("Project initialized successfully!")
                st.session_state[f"initializing_{project.id}"] = False
                st.experimental_rerun()
            
            # Close tab button
            if st.button("Close Tab", key=f"close_{project.id}"):
                # Remove the project from the session state
                if st.session_state.get("selected_project") == project.id:
                    st.session_state.selected_project = None
                
                # Refresh the page to update the tabs
                st.experimental_rerun()

# Render the step-by-step view
def render_step_by_step_view(project):
    """Render a step-by-step view of the project implementation plan."""
    if not project.implementation_plan:
        st.info("No implementation plan found. Initialize the project to generate a plan.")
        return
    
    # Get tasks from the implementation plan
    tasks = project.implementation_plan.get('tasks', [])
    
    if not tasks:
        st.info("No tasks found in the implementation plan.")
        return
    
    # Display tasks in a step-by-step format
    for i, task in enumerate(tasks):
        status = "✓" if task.get('status') == 'completed' else " "
        st.write(f"{i+1}. [{status}] {task.get('title')}")
        
        # Display subtasks if any
        subtasks = task.get('subtasks', [])
        for j, subtask in enumerate(subtasks):
            status = "✓" if subtask.get('status') == 'completed' else " "
            st.write(f"   {i+1}.{j+1}. [{status}] {subtask.get('title')}")

# Render the implementation tree
def render_implementation_tree(project_id):
    """Render the implementation tree for a project."""
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    if not project.implementation_plan:
        st.info("No implementation plan found. Initialize the project to generate a plan.")
        return
    
    # Get tasks from the implementation plan
    tasks = project.implementation_plan.get('tasks', [])
    
    if not tasks:
        st.info("No tasks found in the implementation plan.")
        return
    
    # Calculate progress
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
    
    progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Display progress
    st.write(f"Progress: {progress_percentage:.1f}%")
    
    # Display tasks with completion status
    for i, task in enumerate(tasks):
        status = "✓" if task.get('status') == 'completed' else " "
        st.write(f"{i+1}. [{status}] {task.get('title')}")
        
        # Display subtasks if any
        subtasks = task.get('subtasks', [])
        for j, subtask in enumerate(subtasks):
            status = "✓" if subtask.get('status') == 'completed' else " "
            st.write(f"   {i+1}.{j+1}. [{status}] {subtask.get('title')}")

# Render the chat interface
def render_chat_interface(project_id=None):
    """Render the chat interface."""
    st.subheader("Project Assistant")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    
    if project_id:
        if project_id not in st.session_state.chat_history:
            st.session_state.chat_history[project_id] = []
        chat_history = st.session_state.chat_history[project_id]
        
        project_database = ProjectDatabase()
        project = project_database.get_project(project_id)
        if project:
            st.write(f"Chatting about project: **{project.name}**")
    else:
        if "global" not in st.session_state.chat_history:
            st.session_state.chat_history["global"] = []
        chat_history = st.session_state.chat_history["global"]
        st.write("General chat (no project selected)")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in chat_history:
            if message["role"] == "user":
                st.markdown(f"**You:** {message['content']}")
            elif message["role"] == "assistant":
                st.markdown(f"**Assistant:** {message['content']}")
            elif message["role"] == "system":
                st.info(message["content"])
    
    # Chat input form
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area("Type your message:", key="chat_input", height=100)
        submit_button = st.form_submit_button("Send")
    
    # Process chat input
    if submit_button and user_input:
        chat_history.append({"role": "user", "content": user_input})
        
        # Simple response for demonstration
        response = "I'm here to help with your project. This is a simplified chat interface for demonstration purposes."
        
        chat_history.append({"role": "assistant", "content": response})
        
        st.experimental_rerun()

# Main function
def main():
    # Initialize session state
    initialize_session_state()
    
    # Top navigation bar
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("Projector")
    
    with col2:
        st.button("Settings", key="settings_button")
        st.button("Dashboard", key="dashboard_button")
    
    # Add Project button (top right)
    add_project_col1, add_project_col2 = st.columns([5, 1])
    with add_project_col2:
        if st.button("➕ Add Project", key="add_project_button"):
            st.session_state.show_create_project = True
    
    # Show create project form if button was clicked
    if st.session_state.get("show_create_project", False):
        with st.expander("Create New Project", expanded=True):
            render_create_project_form()
            if st.button("Cancel", key="cancel_create_project"):
                st.session_state.show_create_project = False
    
    # Main content area with 3-column layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # Left column - Step by step structure view
    with col1:
        st.subheader("Step by Step Structure")
        st.write("View generated from user's documents")
        
        # Get the currently selected project
        selected_project_id = st.session_state.get("selected_project")
        if selected_project_id:
            project_database = ProjectDatabase()
            project = project_database.get_project(selected_project_id)
            if project:
                render_step_by_step_view(project)
            else:
                st.info("Select a project to view its step-by-step structure")
        else:
            st.info("Select a project to view its step-by-step structure")
    
    # Middle column - Tabbed project interface
    with col2:
        # Get all projects
        project_database = ProjectDatabase()
        projects = project_database.get_all_projects()
        
        # Render tabbed interface
        render_tabbed_interface(projects)
    
    # Right column - Tree structure view
    with col3:
        st.subheader("Tree Structure View")
        st.write("Component Integration Completion Check Map")
        
        # Get the currently selected project
        selected_project_id = st.session_state.get("selected_project")
        if selected_project_id:
            project_database = ProjectDatabase()
            project = project_database.get_project(selected_project_id)
            if project:
                render_implementation_tree(selected_project_id)
            else:
                st.info("Select a project to view its implementation tree")
        else:
            st.info("Select a project to view its implementation tree")
    
    # Chat interface at the bottom
    st.markdown("---")
    render_chat_interface(st.session_state.get("selected_project"))

if __name__ == "__main__":
    main()
