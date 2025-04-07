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
from projector.frontend.sidebar import render_sidebar
from projector.frontend.merge_ui_components import (
    render_merge_history, render_project_tabs_with_merges
)
from projector.frontend.session_state import initialize_session_state, update_session_data
from projector.frontend.accessibility import render_accessibility_settings, apply_accessibility_styles
from projector.frontend.code_suggestions_ui import render_code_suggestions_ui, render_code_improvement_ui
from projector.frontend.project_ui import render_project_ui
from projector.frontend.resource_management_ui import render_resource_management_ui
from projector.frontend.project_management_ui import render_project_management_ui

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

logger = logging.getLogger(__name__)

# Runtime configuration
def main():
    """Main Streamlit application."""
    # Initialize session state
    initialize_session_state()
    
    # Apply accessibility styles
    apply_accessibility_styles()
    
    # Render the sidebar
    render_sidebar()
    
    # Get the selected page from session state
    page = st.session_state.get("page", "Dashboard")
    
    # Render the selected page
    if page == "Dashboard":
        render_header("Dashboard")
        st.write("Welcome to the MultiThread Slack GitHub Tool!")
        
        # Display project summary
        project_database = ProjectDatabase()
        projects = project_database.list_projects()
        
        st.subheader("Project Summary")
        st.write(f"Total Projects: {len(projects)}")
        
        # Display recent activity
        st.subheader("Recent Activity")
        st.info("No recent activity to display.")
        
    elif page == "Projects":
        render_project_ui()
        
    elif page == "Project Management":
        render_project_management_ui()
        
    elif page == "Document Management":
        render_header("Document Management")
        st.write("Manage project documents here.")
        
    elif page == "Thread Management":
        render_header("Thread Management")
        st.write("Manage Slack threads here.")
        
    elif page == "GitHub Integration":
        render_header("GitHub Integration")
        st.write("Manage GitHub integration here.")
        
    elif page == "Code Suggestions":
        render_code_suggestions_ui()
        
    elif page == "Code Improvements":
        render_code_improvement_ui()
        
    elif page == "Merge History":
        render_merge_history()
        
    elif page == "Resource Management":
        render_resource_management_ui()
        
    elif page == "Settings":
        render_header("Settings")
        
        # Render accessibility settings
        render_accessibility_settings()
        
    elif page == "Help":
        render_header("Help")
        st.write("Need help? Check out the documentation or contact support.")
    
    # Update session data
    update_session_data()

if __name__ == "__main__":
    main()
