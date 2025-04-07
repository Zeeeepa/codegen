import streamlit as st
from datetime import datetime
from projector.backend.project_database import ProjectDatabase

def render_create_project_form():
    """Render a form for creating a new project."""
    with st.form("create_project_form"):
        st.subheader("Create New Project")
        
        name = st.text_input("Project Name")
        description = st.text_area("Description")
        github_repo = st.text_input("GitHub Repository")
        github_branch = st.text_input("GitHub Branch", value="main")
        slack_channel = st.text_input("Slack Channel")
        
        submitted = st.form_submit_button("Create Project")
        
        if submitted:
            if not name:
                st.error("Project name is required.")
                return
            
            # Create project in database
            project_database = ProjectDatabase()
            project_id = project_database.create_project({
                'name': name,
                'description': description,
                'github_repo': github_repo,
                'github_branch': github_branch,
                'slack_channel': slack_channel,
                'status': 'Active',
                'created_at': datetime.now().isoformat()
            })
            
            if project_id:
                st.success(f"Project '{name}' created successfully!")
                # Refresh the project list
                st.session_state.projects = project_database.list_projects()
                return True
            else:
                st.error("Failed to create project.")
                return False