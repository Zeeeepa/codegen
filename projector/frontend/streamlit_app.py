import streamlit as st
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

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
from projector.frontend.ui_components import (
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
runtime_config = {
    "slack_connected": False,
    "github_connected": False,
    "ai_enabled": False,
    "active_channel": SLACK_DEFAULT_CHANNEL,
    "active_repo": GITHUB_DEFAULT_REPO,
    "max_threads": 10
}

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
    
    # Create columns for KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Active Threads", st.session_state.get("thread_count", 0))
    with col2:
        st.metric("Features", st.session_state.get("features_count", 0))
    with col3:
        st.metric("Open PRs", st.session_state.get("open_prs_count", 0))
    with col4:
        st.metric("Documents", st.session_state.get("documents_count", 0))
    with col5:
        st.metric("Merges", st.session_state.get("merges_count", 0))
    
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

def render_merge_management():
    """Render the merge management page."""
    st.title("Merge Management")
    
    # Get current project
    if st.session_state.current_project_id and hasattr(st.session_state, "backend_connector"):
        connector = st.session_state.backend_connector
        project = connector.get_project(st.session_state.current_project_id)
        
        if project:
            render_merge_history(project)
        else:
            st.warning("No project selected. Please select a project from the sidebar.")
    else:
        st.warning("No project selected. Please select a project from the sidebar.")

def render_code_suggestions_page():
    """Render the code suggestions page."""
    st.title("Code Suggestions")
    
    # Create tabs for different code suggestion features
    suggestions_tab, improvement_tab = st.tabs(["Code Analysis", "Code Improvement"])
    
    with suggestions_tab:
        render_code_suggestions_ui()
    
    with improvement_tab:
        render_code_improvement_ui()

def handle_keyboard_shortcuts():
    """Handle keyboard shortcuts for accessibility."""
    # Add JavaScript for keyboard shortcuts
    js_code = """
    <script>
    document.addEventListener('keydown', function(e) {
        // Alt + key combinations
        if (e.altKey) {
            // Alt + 1-9: Navigate to different pages
            if (e.key >= '1' && e.key <= '9') {
                const navItems = document.querySelectorAll('div[data-testid="stRadio"] label');
                const index = parseInt(e.key) - 1;
                if (index < navItems.length) {
                    navItems[index].click();
                }
            }
            
            // Alt + S: Toggle sidebar
            else if (e.key === 's' || e.key === 'S') {
                const sidebarButton = document.querySelector('button[kind="headerNoPadding"]');
                if (sidebarButton) {
                    sidebarButton.click();
                }
            }
            
            // Alt + A: Open accessibility settings
            else if (e.key === 'a' || e.key === 'A') {
                const navItems = document.querySelectorAll('div[data-testid="stRadio"] label');
                for (let i = 0; i < navItems.length; i++) {
                    if (navItems[i].textContent.includes('Accessibility')) {
                        navItems[i].click();
                        break;
                    }
                }
            }
            
            // Alt + D: Toggle dark/light mode
            else if (e.key === 'd' || e.key === 'D') {
                const themeButton = document.querySelector('button[key="toggle_theme"]');
                if (themeButton) {
                    themeButton.click();
                }
            }
            
            // Alt + H: Show help
            else if (e.key === 'h' || e.key === 'H') {
                const helpExpander = document.querySelector('div[aria-controls*="Help & Support"]');
                if (helpExpander) {
                    helpExpander.click();
                }
            }
        }
    });
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)

def add_robustness_features():
    """Add robustness features to the application."""
    # Error boundary
    try:
        # Check for critical components
        if not hasattr(st.session_state, "backend_connector") and st.session_state.authenticated:
            logger.error("Backend connector not initialized but user is authenticated")
            st.session_state.error_message = "Connection error: Backend services unavailable. Please try again."
            
        # Check for connectivity
        if st.session_state.authenticated:
            if not st.session_state.slack_connected:
                logger.warning("Slack connection lost")
                st.session_state.error_message = "Warning: Slack connection lost. Some features may be unavailable."
                
            if not st.session_state.github_connected:
                logger.warning("GitHub connection lost")
                st.session_state.error_message = "Warning: GitHub connection lost. Some features may be unavailable."
    except Exception as e:
        logger.error(f"Error in robustness check: {e}")

def main():
    """Main Streamlit application."""
    try:
        st.set_page_config(
            page_title="MultiThread Slack GitHub Tool",
            page_icon="🔄",
            layout="wide"
        )
        
        # Initialize session state
        initialize_session_state()
        
        # Apply accessibility styles
        apply_accessibility_styles()
        
        # Add keyboard shortcuts
        handle_keyboard_shortcuts()
        
        # Add robustness features
        add_robustness_features()
        
        # Render authentication page if not authenticated
        if not st.session_state.authenticated:
            render_auth_page()
            return
        
        # Update session data from backend
        update_session_data()
        
        # Render sidebar and get selected page
        page = render_sidebar()
        
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
        elif page == "Merge Management":
            render_merge_management()
        elif page == "Code Suggestions":
            render_code_suggestions_page()
        elif page == "Accessibility":
            render_accessibility_settings()
            
    except Exception as e:
        logger.error(f"Unhandled exception in main application: {e}", exc_info=True)
        st.error(f"An unexpected error occurred: {str(e)}")
        st.write("Please try refreshing the page. If the problem persists, contact support.")

if __name__ == "__main__":
    main()
