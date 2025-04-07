import streamlit as st
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# Load environment variables
load_dotenv()

# Import backend components
from agentgen.application.projector.backend.config import (
    SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
    SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO
)
from agentgen.application.projector.backend.slack_manager import SlackManager
from agentgen.application.projector.backend.github_manager import GitHubManager
from agentgen.application.projector.backend.project_database import ProjectDatabase
from agentgen.application.projector.backend.project_manager import ProjectManager
from agentgen.application.projector.backend.thread_pool import ThreadPool
from agentgen.application.projector.frontend.ui_components import (
    render_header, render_sidebar, render_project_list,
    render_project_details, render_create_project_form
)
from agentgen.application.projector.frontend.session_state import initialize_session_state

# Import from API connectors
from agentgen.application.projector.api.api_connectors import BackendConnector

# Runtime configuration
runtime_config = {
    "slack_connected": False,
    "github_connected": False,
    "ai_enabled": False,
    "active_channel": SLACK_DEFAULT_CHANNEL,
    "active_repo": GITHUB_DEFAULT_REPO,
    "max_threads": 10
}

# Initialize session state
def initialize_session_state():
    """Initialize the session state with default values."""
    # Authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # Connection states
    if "slack_connected" not in st.session_state:
        st.session_state.slack_connected = False
    
    if "github_connected" not in st.session_state:
        st.session_state.github_connected = False
    
    # Credentials
    if "slack_token" not in st.session_state:
        st.session_state.slack_token = ""
    
    if "slack_channel" not in st.session_state:
        st.session_state.slack_channel = "general"
    
    if "github_token" not in st.session_state:
        st.session_state.github_token = ""
    
    if "github_username" not in st.session_state:
        st.session_state.github_username = ""
    
    if "github_repo" not in st.session_state:
        st.session_state.github_repo = ""
    
    # AI settings
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""
    
    if "ai_enabled" not in st.session_state:
        st.session_state.ai_enabled = runtime_config.get("ai_enabled", False)
    
    # Data counters
    if "thread_count" not in st.session_state:
        st.session_state.thread_count = 0
    
    if "features_count" not in st.session_state:
        st.session_state.features_count = 0
    
    if "documents_count" not in st.session_state:
        st.session_state.documents_count = 0
    
    if "open_prs_count" not in st.session_state:
        st.session_state.open_prs_count = 0
    
    # Backend connector
    if "backend_connector" not in st.session_state:
        st.session_state.backend_connector = None
    
    # Current project
    if "current_project_id" not in st.session_state:
        st.session_state.current_project_id = None

def update_session_data():
    """Update session data from backend."""
    if hasattr(st.session_state, "backend_connector") and st.session_state.backend_connector:
        connector = st.session_state.backend_connector
        
        # Update thread count
        threads = connector.get_threads()
        st.session_state.thread_count = len(threads) if threads else 0
        
        # Update features count
        features = connector.get_features()
        st.session_state.features_count = len(features) if features else 0
        
        # Update documents count
        documents = connector.list_documents()
        st.session_state.documents_count = len(documents) if documents else 0
        
        # Update PRs count
        pull_requests = connector.list_pull_requests()
        open_prs = [pr for pr in pull_requests if pr.get("state") == "open"]
        st.session_state.open_prs_count = len(open_prs) if open_prs else 0

def render_auth_page():
    """Render the authentication page."""
    st.title("Authentication")
    st.write("Please enter your credentials to continue.")
    
    # Placeholder for authentication form
    st.write("Authentication form would go here.")
    
    # For development, allow skipping authentication
    if st.button("Skip Authentication (Development Only)"):
        st.session_state.authenticated = True
        st.experimental_rerun()

def render_dashboard():
    """Render the dashboard page."""
    st.title("Dashboard")
    st.write("Welcome to the MultiThread Slack GitHub Tool!")
    
    # Placeholder for dashboard content
    st.write("Dashboard content would go here.")

def render_document_management():
    """Render the document management page."""
    st.title("Document Management")
    
    # Placeholder for document management content
    st.write("Document management content would go here.")

def render_thread_management():
    """Render the thread management page."""
    st.title("Thread Management")
    
    # Placeholder for thread management content
    st.write("Thread management content would go here.")

def render_github_panel():
    """Render the GitHub integration panel."""
    st.title("GitHub Integration")
    
    # Placeholder for GitHub integration content
    st.write("GitHub integration content would go here.")

def render_planning_page(planning_manager, project_database):
    """Render the project planning page."""
    st.title("Project Planning")
    
    # Placeholder for project planning content
    st.write("Project planning content would go here.")

def render_ai_assistant_panel(ai_assistant):
    """Render the AI assistant panel."""
    st.title("AI Assistant")
    
    # Placeholder for AI assistant content
    st.write("AI assistant content would go here.")

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="MultiThread Slack GitHub Tool",
        page_icon="🔄",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Render authentication page if not authenticated
    if not st.session_state.authenticated:
        render_auth_page()
        return
    
    # Update session data from backend
    # update_session_data()
    
    # Render sidebar and get selected page
    # page = render_sidebar()
    page = "Dashboard"  # Default to dashboard for now
    
    # Render selected page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Document Management":
        render_document_management()
    elif page == "Thread Management":
        render_thread_management()
    elif page == "GitHub Integration":
        render_github_panel()
    elif page == "Project Planning":
        render_planning_page(None, None)  # Placeholder for now
    elif page == "AI Assistant":
        render_ai_assistant_panel(None)  # Placeholder for now

if __name__ == "__main__":
    main()
