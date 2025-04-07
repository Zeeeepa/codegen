import streamlit as st

def render_project_details(project):
    """Render detailed information about a project."""
    if not project:
        st.warning("No project selected.")
        return
    
    st.subheader(project['name'])
    st.write(f"**ID:** {project['id']}")
    st.write(f"**Description:** {project.get('description', 'No description')}")
    st.write(f"**Status:** {project.get('status', 'Unknown')}")
    st.write(f"**Created:** {project.get('created_at', 'Unknown')}")
    
    # Display GitHub information if available
    if 'github_repo' in project:
        st.subheader("GitHub Repository")
        st.write(f"**Repository:** {project['github_repo']}")
        if 'github_branch' in project:
            st.write(f"**Branch:** {project['github_branch']}")
    
    # Display Slack information if available
    if 'slack_channel' in project:
        st.subheader("Slack Channel")
        st.write(f"**Channel:** {project['slack_channel']}")