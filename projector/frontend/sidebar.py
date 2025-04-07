"""
Sidebar UI component for the projector application.
"""
import streamlit as st

def render_sidebar():
    """Render the sidebar navigation."""
    st.sidebar.title("MultiThread Slack GitHub")
    
    # Profile section with connection status
    with st.sidebar.expander("👤 Connection Status", expanded=True):
        if st.session_state.authenticated:
            st.success("✅ **Authenticated**")
            
            # Slack status
            if st.session_state.slack_connected:
                st.success("Connected to Slack")
            else:
                st.error("Disconnected from Slack")
                
            # GitHub status
            if st.session_state.github_connected:
                st.success("Connected to GitHub")
            else:
                st.error("Disconnected from GitHub")
                
            if st.button("Logout", key="logout"):
                st.session_state.authenticated = False
                st.experimental_rerun()
        else:
            st.warning("❌ **Not Authenticated**")
    
    # Navigation
    st.sidebar.header("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Dashboard", "Document Management", "Thread Management", "GitHub Integration", 
         "Project Planning", "AI Assistant", "Merge Management"]
    )
    
    # Project selector (if authenticated)
    if st.session_state.authenticated and hasattr(st.session_state, "backend_connector"):
        with st.sidebar.expander("📂 Projects", expanded=True):
            projects = st.session_state.backend_connector.list_projects()
            project_names = ["Select Project"] + [p.name for p in projects]
            
            selected_index = 0
            if st.session_state.get("current_project_id"):
                for i, project in enumerate(projects):
                    if project.id == st.session_state.current_project_id:
                        selected_index = i + 1  # +1 because of "Select Project"
                        break
            
            selected_project = st.selectbox(
                "Active Project", 
                project_names, 
                index=selected_index
            )
            
            if selected_project != "Select Project":
                for project in projects:
                    if project.name == selected_project:
                        st.session_state.current_project_id = project.id
                        break
            
            if st.button("New Project"):
                st.session_state.show_new_project_form = True
    
    # Statistics in sidebar
    if st.session_state.authenticated:
        with st.sidebar.expander("📊 Statistics", expanded=False):
            st.metric("Active Threads", st.session_state.get("thread_count", 0))
            st.metric("Features in Progress", st.session_state.get("features_count", 0))
            st.metric("Documents", st.session_state.get("documents_count", 0))
            st.metric("Open PRs", st.session_state.get("open_prs_count", 0))
            st.metric("Merges", st.session_state.get("merges_count", 0))
    
    return page
