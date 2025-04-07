import streamlit as st

def render_project_list(projects):
    """Render a list of projects."""
    if not projects:
        st.info("No projects found.")
        return
    
    for project in projects:
        with st.expander(f"{project['name']} ({project['id']})"):
            st.write(f"**Description:** {project.get('description', 'No description')}")
            st.write(f"**Status:** {project.get('status', 'Unknown')}")
            st.write(f"**Created:** {project.get('created_at', 'Unknown')}")
            
            if st.button("View Details", key=f"view_{project['id']}"):
                st.session_state.selected_project = project
                st.session_state.page = "Project Details"
                st.experimental_rerun()