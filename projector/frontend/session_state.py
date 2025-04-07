import streamlit as st
import time

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