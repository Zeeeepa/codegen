"""
Sidebar UI component for the projector application.
"""
import streamlit as st
from .session_state import toggle_theme, toggle_sidebar, clear_messages

def render_sidebar():
    """Render the sidebar navigation."""
    st.sidebar.title("MultiThread Slack GitHub")
    
    # Error and success messages
    if st.session_state.error_message:
        st.sidebar.error(st.session_state.error_message)
        if st.sidebar.button("Clear Error", key="clear_error"):
            clear_messages()
            st.rerun()
    
    if st.session_state.success_message:
        st.sidebar.success(st.session_state.success_message)
        if st.sidebar.button("Clear Message", key="clear_success"):
            clear_messages()
            st.rerun()
    
    # Theme toggle
    theme_col1, theme_col2 = st.sidebar.columns([3, 1])
    with theme_col1:
        st.write(f"Theme: **{st.session_state.theme.capitalize()}**")
    with theme_col2:
        if st.button("🌓", key="toggle_theme", help="Toggle light/dark theme"):
            toggle_theme()
            st.rerun()
    
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
        ["Dashboard", "Projects", "Project Management", "Document Management", "Thread Management", "GitHub Integration", 
         "Project Planning", "Resource Management", "AI Assistant", "Merge History", "Code Suggestions", 
         "Code Improvements", "Settings", "Help"]
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
            st.metric("Team Members", st.session_state.get("team_members_count", 0))
    
    # Quick accessibility options
    with st.sidebar.expander("🌐 Quick Accessibility", expanded=False):
        # Font size buttons in a row
        st.write("Font Size:")
        font_col1, font_col2, font_col3 = st.columns(3)
        with font_col1:
            st.button("A", key="small_font_sidebar", help="Small font")
        with font_col2:
            st.button("A", key="medium_font_sidebar", help="Medium font")
        with font_col3:
            st.button("A", key="large_font_sidebar", help="Large font", 
                     use_container_width=True)
        
        # High contrast toggle
        high_contrast = st.checkbox(
            "High Contrast", 
            value=st.session_state.high_contrast,
            help="Enable high contrast mode for better visibility"
        )
        if high_contrast != st.session_state.high_contrast:
            st.session_state.high_contrast = high_contrast
            st.rerun()
        
        # Reduced motion toggle
        reduced_motion = st.checkbox(
            "Reduced Motion", 
            value=st.session_state.reduced_motion,
            help="Reduce animations and motion effects"
        )
        if reduced_motion != st.session_state.reduced_motion:
            st.session_state.reduced_motion = reduced_motion
            st.rerun()
    
    # Help and support
    with st.sidebar.expander("❓ Help & Support", expanded=False):
        st.write("**Documentation**")
        st.markdown("[View Documentation](https://github.com/Zeeeepa/codegen/tree/main/projector)")
        
        st.write("**Report Issues**")
        st.markdown("[Report a Bug](https://github.com/Zeeeepa/codegen/issues/new)")
        
        st.write("**Version**")
        st.write("v1.0.0")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<div style='text-align: center; color: gray; font-size: 0.8em;'>"
        "© 2025 MultiThread Slack GitHub Tool"
        "</div>", 
        unsafe_allow_html=True
    )
    
    # Update the page in session state
    st.session_state.page = page
    
    return page
