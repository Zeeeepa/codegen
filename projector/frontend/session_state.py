import streamlit as st
import time
import logging

def initialize_session_state():
    """Initialize the session state with default values."""
    # Set up logging
    logger = logging.getLogger(__name__)
    
    try:
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
            st.session_state.ai_enabled = False
            
        # UI state
        if "theme" not in st.session_state:
            st.session_state.theme = "light"
            
        if "sidebar_collapsed" not in st.session_state:
            st.session_state.sidebar_collapsed = False
            
        if "show_new_project_form" not in st.session_state:
            st.session_state.show_new_project_form = False
            
        if "current_tab" not in st.session_state:
            st.session_state.current_tab = "Overview"
        
        # Data counters
        if "thread_count" not in st.session_state:
            st.session_state.thread_count = 0
        
        if "features_count" not in st.session_state:
            st.session_state.features_count = 0
        
        if "documents_count" not in st.session_state:
            st.session_state.documents_count = 0
        
        if "open_prs_count" not in st.session_state:
            st.session_state.open_prs_count = 0
            
        if "merges_count" not in st.session_state:
            st.session_state.merges_count = 0
        
        # Backend connector
        if "backend_connector" not in st.session_state:
            st.session_state.backend_connector = None
            
        # Current project
        if "current_project_id" not in st.session_state:
            st.session_state.current_project_id = None
            
        # Error handling
        if "error_message" not in st.session_state:
            st.session_state.error_message = None
            
        if "success_message" not in st.session_state:
            st.session_state.success_message = None
            
        # Accessibility settings
        if "font_size" not in st.session_state:
            st.session_state.font_size = "medium"  # Options: small, medium, large
            
        if "high_contrast" not in st.session_state:
            st.session_state.high_contrast = False
            
        if "reduced_motion" not in st.session_state:
            st.session_state.reduced_motion = False
            
        logger.info("Session state initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing session state: {e}")
        # Ensure basic state is set even if there's an error
        if "error_message" not in st.session_state:
            st.session_state.error_message = f"Error initializing application: {str(e)}"

def update_session_data():
    """Update session data from backend."""
    logger = logging.getLogger(__name__)
    
    try:
        if hasattr(st.session_state, "backend_connector") and st.session_state.backend_connector:
            connector = st.session_state.backend_connector
            
            # Update thread count
            try:
                threads = connector.get_threads()
                st.session_state.thread_count = len(threads) if threads else 0
            except Exception as e:
                logger.warning(f"Error updating thread count: {e}")
                st.session_state.thread_count = 0
            
            # Update features count
            try:
                features = connector.get_features()
                st.session_state.features_count = len(features) if features else 0
            except Exception as e:
                logger.warning(f"Error updating features count: {e}")
                st.session_state.features_count = 0
            
            # Update documents count
            try:
                documents = connector.list_documents()
                st.session_state.documents_count = len(documents) if documents else 0
            except Exception as e:
                logger.warning(f"Error updating documents count: {e}")
                st.session_state.documents_count = 0
            
            # Update PRs count
            try:
                pull_requests = connector.list_pull_requests()
                open_prs = [pr for pr in pull_requests if pr.get("state") == "open"]
                st.session_state.open_prs_count = len(open_prs) if open_prs else 0
            except Exception as e:
                logger.warning(f"Error updating PRs count: {e}")
                st.session_state.open_prs_count = 0
                
            # Update merges count
            try:
                if st.session_state.current_project_id:
                    project = connector.get_project(st.session_state.current_project_id)
                    if project and hasattr(project, 'merges'):
                        st.session_state.merges_count = len(project.merges)
                    else:
                        st.session_state.merges_count = 0
            except Exception as e:
                logger.warning(f"Error updating merges count: {e}")
                st.session_state.merges_count = 0
                
            logger.info("Session data updated successfully")
    except Exception as e:
        logger.error(f"Error updating session data: {e}")
        st.session_state.error_message = f"Error updating data: {str(e)}"

def clear_messages():
    """Clear error and success messages."""
    st.session_state.error_message = None
    st.session_state.success_message = None

def set_error_message(message):
    """Set an error message to display to the user."""
    st.session_state.error_message = message
    
def set_success_message(message):
    """Set a success message to display to the user."""
    st.session_state.success_message = message

def toggle_theme():
    """Toggle between light and dark theme."""
    if st.session_state.theme == "light":
        st.session_state.theme = "dark"
    else:
        st.session_state.theme = "light"

def toggle_sidebar():
    """Toggle sidebar collapsed state."""
    st.session_state.sidebar_collapsed = not st.session_state.sidebar_collapsed

def set_font_size(size):
    """Set the font size for accessibility."""
    if size in ["small", "medium", "large"]:
        st.session_state.font_size = size

def toggle_high_contrast():
    """Toggle high contrast mode for accessibility."""
    st.session_state.high_contrast = not st.session_state.high_contrast

def toggle_reduced_motion():
    """Toggle reduced motion for accessibility."""
    st.session_state.reduced_motion = not st.session_state.reduced_motion