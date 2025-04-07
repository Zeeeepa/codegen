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
from projector.frontend.tree_view import render_implementation_tree
from projector.frontend.chat_interface import render_chat_interface

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

def render_multi_project_tabs():
    """Render tabs for all active projects."""
    project_database = ProjectDatabase()
    projects = project_database.list_projects()
    
    if not projects:
        st.info("No projects found. Create a new project to get started.")
        return
    
    # Create tabs for each project
    project_names = [p.name for p in projects]
    tabs = st.tabs(project_names)
    
    # Store the selected tab index in session state if not already set
    if "selected_tab_index" not in st.session_state:
        st.session_state.selected_tab_index = 0
    
    # Render content for each tab
    for i, tab in enumerate(tabs):
        with tab:
            # Update the selected tab index when a tab is clicked
            if i != st.session_state.selected_tab_index:
                st.session_state.selected_tab_index = i
                st.session_state.selected_project = projects[i].id
            
            # Render the project content
            render_project_content(projects[i])

def render_project_content(project):
    """Render the content for a specific project tab."""
    st.subheader(f"Project: {project.name}")
    
    # Project metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Repository:** {project.git_url}")
    with col2:
        st.write(f"**Slack Channel:** {project.slack_channel or 'Default'}")
    with col3:
        st.write(f"**Concurrency:** {project.max_parallel_tasks}")
    
    # Project tabs
    project_tabs = st.tabs(["Overview", "Documents", "Implementation", "Settings"])
    
    with project_tabs[0]:  # Overview
        st.write("### Project Overview")
        st.write(f"**Created:** {project.created_at}")
        st.write(f"**Last Updated:** {project.updated_at}")
        
        # Display documents count
        st.write(f"**Documents:** {len(project.documents)}")
        
        # Display implementation plan status
        if project.implementation_plan:
            tasks = project.implementation_plan.get('tasks', [])
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            st.write(f"**Implementation Progress:** {progress:.1f}%")
            st.progress(progress / 100)
        else:
            st.info("No implementation plan found. Generate a plan to track progress.")
    
    with project_tabs[1]:  # Documents
        st.write("### Project Documents")
        if not project.documents:
            st.info("No documents found. Upload documents to get started.")
        else:
            for doc in project.documents:
                st.write(f"- {os.path.basename(doc)}")
            
            # Document upload
            st.write("### Upload New Document")
            uploaded_file = st.file_uploader(
                "Upload Document",
                type=["md", "txt", "pdf", "docx"],
                key=f"doc_upload_{project.id}"
            )
            
            if uploaded_file:
                doc_category = st.selectbox(
                    "Document Category",
                    ["Requirements", "Architecture", "Implementation", "Testing", "Other"],
                    key=f"doc_category_{project.id}"
                )
                
                if st.button("Save Document", key=f"save_doc_{project.id}"):
                    # Save document logic
                    docs_dir = os.path.join("docs", project.name, doc_category.lower())
                    os.makedirs(docs_dir, exist_ok=True)
                    
                    file_path = os.path.join(docs_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Add to project
                    project_database = ProjectDatabase()
                    if project_database.add_document_to_project(project.id, file_path):
                        st.success(f"Document '{uploaded_file.name}' uploaded successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to add document to project.")
    
    with project_tabs[2]:  # Implementation
        st.write("### Implementation Plan")
        
        # Check if the project has an implementation plan
        if not project.implementation_plan:
            st.info("No implementation plan found. Generate a plan to get started.")
            
            if st.button("Generate Implementation Plan", key=f"gen_plan_{project.id}"):
                # Initialize AI User Agent
                from projector.backend.slack_manager import SlackManager
                from projector.backend.github_manager import GitHubManager
                from projector.backend.thread_pool import ThreadPool
                from projector.backend.project_manager import ProjectManager
                from projector.backend.ai_user_agent import AIUserAgent
                from projector.backend.config import (
                    SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
                    SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO
                )
                
                # Initialize components
                github_manager = GitHubManager(
                    github_token=GITHUB_TOKEN,
                    github_username=GITHUB_USERNAME,
                    default_repo=GITHUB_DEFAULT_REPO
                )
                
                slack_manager = SlackManager(
                    slack_token=SLACK_USER_TOKEN,
                    default_channel=SLACK_DEFAULT_CHANNEL
                )
                
                thread_pool = ThreadPool(max_threads=10)
                
                project_manager = ProjectManager(
                    github_manager=github_manager,
                    slack_manager=slack_manager,
                    thread_pool=thread_pool
                )
                
                project_database = ProjectDatabase()
                
                ai_user_agent = AIUserAgent(
                    slack_manager=slack_manager,
                    github_manager=github_manager,
                    project_database=project_database,
                    project_manager=project_manager,
                    thread_pool=thread_pool,
                    docs_path="docs"
                )
                
                # Generate the implementation plan
                with st.spinner("Generating implementation plan..."):
                    implementation_plan = ai_user_agent.create_implementation_plan(project.id)
                    
                    if implementation_plan:
                        st.success("Implementation plan generated successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to generate implementation plan.")
        else:
            # Display the implementation tree
            render_implementation_tree(project.id)
    
    with project_tabs[3]:  # Settings
        st.write("### Project Settings")
        
        # Concurrency settings
        st.write("#### Concurrency Settings")
        project_database = ProjectDatabase()
        
        new_concurrency = st.slider(
            "Maximum Concurrent Tasks",
            min_value=1,
            max_value=10,
            value=project.max_parallel_tasks,
            help="Set the maximum number of tasks that can be processed concurrently.",
            key=f"concurrency_{project.id}"
        )
        
        if new_concurrency != project.max_parallel_tasks:
            if st.button("Update Concurrency", key=f"update_concurrency_{project.id}"):
                project.max_parallel_tasks = new_concurrency
                if project_database.save_project(project):
                    st.success(f"Concurrency updated to {new_concurrency} tasks.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to update concurrency settings.")
        
        # Slack channel settings
        st.write("#### Slack Integration")
        new_slack_channel = st.text_input(
            "Slack Channel",
            value=project.slack_channel or "",
            help="Set the Slack channel for project notifications.",
            key=f"slack_channel_{project.id}"
        )
        
        if new_slack_channel != project.slack_channel:
            if st.button("Update Slack Channel", key=f"update_slack_{project.id}"):
                project.slack_channel = new_slack_channel
                if project_database.save_project(project):
                    st.success(f"Slack channel updated to {new_slack_channel}.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to update Slack channel.")
        
        # GitHub repository settings
        st.write("#### GitHub Integration")
        new_git_url = st.text_input(
            "GitHub Repository URL",
            value=project.git_url,
            help="Set the GitHub repository URL for the project.",
            key=f"git_url_{project.id}"
        )
        
        if new_git_url != project.git_url:
            if st.button("Update GitHub URL", key=f"update_git_{project.id}"):
                project.git_url = new_git_url
                if project_database.save_project(project):
                    st.success(f"GitHub URL updated to {new_git_url}.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to update GitHub URL.")
        
        # Danger zone
        st.write("#### Danger Zone")
        if st.button("Delete Project", key=f"delete_{project.id}"):
            confirm = st.checkbox("Confirm deletion", key=f"confirm_delete_{project.id}")
            if confirm:
                project_database = ProjectDatabase()
                if project_database.delete_project(project.id):
                    st.success(f"Project '{project.name}' deleted successfully!")
                    st.session_state.pop("selected_project", None)
                    st.session_state.pop("selected_tab_index", None)
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete project.")

# Runtime configuration
def main():
    """Main Streamlit application."""
    # Initialize session state
    initialize_session_state()
    
    # Apply accessibility styles
    apply_accessibility_styles()
    
    # Main layout with three columns
    left_col, main_col, right_col = st.columns([1, 2, 1])
    
    with left_col:
        # Render the sidebar in the left column
        render_sidebar()
    
    with main_col:
        # Get the selected page from session state
        page = st.session_state.get("page", "Dashboard")
        
        # Render the selected page
        if page == "Dashboard":
            render_header("Dashboard")
            
            # Add Project button
            if st.button("➕ Add Project", key="add_project_button"):
                st.session_state.page = "Project Management"
                st.experimental_rerun()
            
            # Render multi-project tabs
            render_multi_project_tabs()
            
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
    
    with right_col:
        # Render the implementation tree in the right column
        if "selected_project" in st.session_state:
            project_id = st.session_state.selected_project
            project_database = ProjectDatabase()
            project = project_database.get_project(project_id)
            
            if project and project.implementation_plan:
                st.write("### Implementation Progress")
                render_implementation_tree(project_id, compact=True)
    
    # Render chat interface at the bottom
    st.write("---")
    render_chat_interface(
        project_id=st.session_state.get("selected_project")
    )
    
    # Update session data
    update_session_data()

if __name__ == "__main__":
    main()
