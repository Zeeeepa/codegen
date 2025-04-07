"""
Streamlit application for the Projector system.
This is a simplified implementation of the UI mockup.
"""
import streamlit as st
import os
import json
import time
import uuid
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Projector - Project Management",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
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
        self.max_parallel_tasks = 2  # Default concurrency
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
            print(f"Error reading database: {e}")
            self.projects = {}
    
    def _write_database(self, data):
        """Write the database to disk."""
        try:
            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            with open(self.db_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error writing database: {e}")
    
    def save_project(self, project):
        """Save a project to the database."""
        # Update the project's updated_at timestamp
        project.updated_at = datetime.now().isoformat()
        
        # Read the current database
        data = {}
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r') as f:
                data = json.load(f)
        
        # Update the project data
        data[project.id] = project.to_dict()
        
        # Write the updated database
        self._write_database(data)
        
        # Update the in-memory projects
        self.projects[project.id] = project
        
        return True
    
    def get_project(self, project_id):
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def get_all_projects(self):
        """Get all projects as a list."""
        return list(self.projects.values())
    
    def delete_project(self, project_id):
        """Delete a project by ID."""
        # Read the current database
        if os.path.exists(self.db_file):
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
    
    def create_project(self, name, git_url, slack_channel=None):
        """Create a new project."""
        # Create a new project
        project = Project(
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
    with st.form("create_project_form"):
        st.subheader("Create New Project")
        
        # Project name
        name = st.text_input("Project Name")
        
        # GitHub URL
        git_url = st.text_input("GitHub Repository URL")
        
        # Slack channel
        slack_channel = st.text_input("Slack Channel ID (optional)")
        
        # Submit button
        submitted = st.form_submit_button("Create Project")
        
        if submitted:
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

# Render the implementation tree view
def render_implementation_tree(project):
    """Render the implementation tree view."""
    if not project.implementation_plan:
        st.info("No implementation plan found. Initialize the project to generate a plan.")
        return
    
    # Sample implementation tree based on the mockup
    st.markdown("""
    ### Implementation Progress
    
    E-Commerce Platform  [65%]
    ├── User Authentication [✓]
    │   ├── Database Schema [✓]
    │   ├── Basic Auth Endpoints [✓]
    │   ├── Social Login [✓]
    │   ├── Password Reset [✓]
    │   └── Two-Factor Auth [ ]
    ├── Product Catalog [75%]
    │   ├── Database Schema [✓]
    │   ├── Basic CRUD API [✓]
    │   ├── Search Functionality [✓]
    │   ├── Filtering Options [ ]
    │   └── Sorting Options [ ]
    ├── Shopping Cart [50%]
    │   ├── Database Schema [✓]
    │   ├── Add/Remove Items [✓]
    │   ├── Update Quantities [ ]
    │   ├── Save for Later [ ]
    │   └── Cart Recovery [ ]
    └── Checkout Process [0%]
        ├── Payment Integration [ ]
        ├── Order Confirmation [ ]
        ├── Email Notifications [ ]
        └── Order History [ ]
    """)

# Render the step-by-step view
def render_step_by_step_view(project):
    """Render a step-by-step view of the project implementation plan."""
    if not project.implementation_plan:
        st.info("No implementation plan found. Initialize the project to generate a plan.")
        return
    
    # Sample step-by-step view based on the mockup
    st.markdown("""
    ### Implementation Steps
    
    1. [✓] Setup Project Structure
       - Initialize repository
       - Configure development environment
       - Set up CI/CD pipeline
    
    2. [✓] User Authentication Module
       - Implement database schema
       - Create authentication endpoints
       - Add social login integration
       - Implement password reset functionality
    
    3. [ ] Product Catalog Module
       - Design database schema
       - Implement CRUD operations
       - Add search functionality
       - Implement filtering and sorting
    
    4. [ ] Shopping Cart Module
       - Design cart data structure
       - Implement add/remove functionality
       - Add quantity updates
       - Implement save for later feature
    
    5. [ ] Checkout Process
       - Integrate payment gateway
       - Implement order confirmation
       - Set up email notifications
       - Create order history view
    """)

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

# Render the implementation plan generator
def render_implementation_plan_generator():
    """Render the implementation plan generator."""
    st.markdown("""
    ### Implementation Plan Generator
    
    Feature: [Two-Factor Authentication                    ]
    Description:
    [Implement TOTP-based two-factor authentication for    ]
    [enhanced security with backup codes and device        ]
    [remembering functionality.                            ]
    
    Dependencies:
    [✓] User Authentication Module
    [ ] Add New Dependencies...
    
    Estimated Complexity: [Medium ▼]
    Priority: [High ▼]
    Assignee: [@john ▼]
    
    Generated Plan:
    
    1. Update User Schema
       - Add TOTP secret field
       - Add backup codes field
       - Add 2FA enabled flag
    
    2. Implement TOTP Generation
       - Add pyotp library
       - Create secret generation function
       - Implement QR code generation
    
    3. Create API Endpoints
       - Enable/disable 2FA endpoint
       - Verify TOTP code endpoint
       - Generate backup codes endpoint
    
    4. Update Login Flow
       - Modify authentication process
       - Add 2FA verification step
       - Implement remember device functionality
    
    5. Create Frontend Components
       - 2FA setup page
       - TOTP verification modal
       - Backup codes display
    
    6. Testing and Documentation
       - Unit tests for all components
       - Integration tests for the flow
       - User documentation
    
    Total Estimated Time: 13 days
    Suggested Deadline: 2025-04-20
    
    [Generate Code Stubs] [Add to Project] [Export Plan]
    """)

# Render the tabbed interface for projects
def render_project_tabs(projects):
    """Render a tabbed interface for projects with closable tabs."""
    if not projects:
        st.info("No projects found. Create a new project to get started.")
        return
    
    # Get the currently selected project ID
    selected_project_id = st.session_state.get("selected_project")
    
    # Create a list of project names for tabs
    project_names = [f"{project.name}[X]" for project in projects]
    
    # Create tabs
    tabs = st.tabs(project_names)
    
    # Render content for each tab
    for i, tab in enumerate(tabs):
        with tab:
            project = projects[i]
            
            # Set the selected project when a tab is clicked
            if selected_project_id != project.id:
                st.session_state.selected_project = project.id
            
            # Project settings and concurrency
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**Project:** {project.name}")
                
            with col2:
                concurrency = st.number_input(
                    "Concurrency",
                    min_value=1,
                    max_value=10,
                    value=project.max_parallel_tasks,
                    key=f"concurrency_{project.id}"
                )
                
                if concurrency != project.max_parallel_tasks:
                    project.max_parallel_tasks = concurrency
                    project_database = ProjectDatabase()
                    project_database.save_project(project)
            
            with col3:
                if st.button("Project Settings", key=f"settings_{project.id}"):
                    st.session_state[f"show_settings_{project.id}"] = True
            
            # Project settings dialog
            if st.session_state.get(f"show_settings_{project.id}", False):
                with st.expander("Project Settings", expanded=True):
                    with st.form(key=f"project_settings_{project.id}"):
                        name = st.text_input("Project Name", value=project.name)
                        git_url = st.text_input("GitHub Repository URL", value=project.git_url)
                        slack_channel = st.text_input("Slack Channel ID", value=project.slack_channel or "")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            save = st.form_submit_button("Save")
                        with col2:
                            cancel = st.form_submit_button("Cancel")
                        
                        if save:
                            project.name = name
                            project.git_url = git_url
                            project.slack_channel = slack_channel
                            
                            project_database = ProjectDatabase()
                            project_database.save_project(project)
                            
                            st.session_state[f"show_settings_{project.id}"] = False
                            st.experimental_rerun()
                        
                        if cancel:
                            st.session_state[f"show_settings_{project.id}"] = False
                            st.experimental_rerun()
            
            # Project content
            st.write("Project's context document view")
            
            # Display documents if available
            if project.documents:
                for doc in project.documents:
                    st.write(f"- {os.path.basename(doc)}")
            else:
                st.info("No documents uploaded yet. Upload documents to get started.")
            
            # Initialize button
            if not project.implementation_plan:
                if st.button("Initialize", key=f"initialize_{project.id}"):
                    st.session_state[f"initializing_{project.id}"] = True
            
            # Simulate initialization
            if st.session_state.get(f"initializing_{project.id}", False):
                with st.spinner("Initializing project..."):
                    # Simulate initialization with a delay
                    time.sleep(2)
                    
                    # Create a sample implementation plan
                    project.implementation_plan = {
                        "initialized": True,
                        "tasks": [
                            {
                                "id": "task1",
                                "title": "Setup project structure",
                                "status": "completed"
                            },
                            {
                                "id": "task2",
                                "title": "Implement core functionality",
                                "status": "in_progress"
                            },
                            {
                                "id": "task3",
                                "title": "Create user interface",
                                "status": "not_started"
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

# Main function
def main():
    # Initialize session state
    initialize_session_state()
    
    # Top navigation bar
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.button("Settings", key="settings_button")
        st.button("Dashboard", key="dashboard_button")
    
    with col3:
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
        render_project_tabs(projects)
    
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
                render_implementation_tree(project)
            else:
                st.info("Select a project to view its implementation tree")
        else:
            st.info("Select a project to view its implementation tree")
    
    # Chat interface at the bottom
    st.markdown("---")
    render_chat_interface(st.session_state.get("selected_project"))

if __name__ == "__main__":
    main()
