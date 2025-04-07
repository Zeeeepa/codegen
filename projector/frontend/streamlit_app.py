import streamlit as st
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Add the src directory to the Python path for codegen modules
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Load environment variables
load_dotenv()

# Import backend components
from projector.backend.config import (
    SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
    SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO
)
from projector.backend.slack_manager import SlackManager
from projector.backend.github_manager import GitHubManager
from projector.backend.project_database import ProjectDatabase
from projector.backend.project_manager import ProjectManager
from projector.backend.thread_pool import ThreadPool

# Import UI components
from projector.frontend.components import (
    render_header, render_project_list,
    render_project_details, render_create_project_form
)
from projector.frontend.session_state import initialize_session_state, update_session_data
from projector.frontend.accessibility import render_accessibility_settings, apply_accessibility_styles
from projector.frontend.tree_view import render_implementation_tree
from projector.frontend.chat_interface import render_chat_interface
from projector.frontend.project_tabs import render_tabbed_interface, render_step_by_step_view

# Import from API connectors
from projector.api.api_connectors import BackendConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("projector/app.log"),
        logging.StreamHandler()
    ]
)

# Initialize session state
initialize_session_state()

# Set page config
st.set_page_config(
    page_title="Projector - Project Management",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply accessibility styles
apply_accessibility_styles()

# Initialize backend components
project_database = ProjectDatabase()
github_manager = GitHubManager(GITHUB_TOKEN, GITHUB_USERNAME)
slack_manager = SlackManager(SLACK_USER_TOKEN, SLACK_DEFAULT_CHANNEL)
thread_pool = ThreadPool(max_workers=10)
project_manager = ProjectManager(github_manager, slack_manager, thread_pool)

# Main layout
def main():
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
