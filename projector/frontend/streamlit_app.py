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
from projector.frontend.session_state import initialize_session_state, update_session_data
from projector.frontend.accessibility import render_accessibility_settings, apply_accessibility_styles
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

def render_recent_activity():
    """Render the recent activity dashboard."""
    st.subheader("Recent Activity")
    
    # Get recent merges from GitHub
    github_manager = GitHubManager(
        github_token=GITHUB_TOKEN,
        github_username=GITHUB_USERNAME,
        default_repo=GITHUB_DEFAULT_REPO
    )
    
    # Get recent merges for all projects
    project_database = ProjectDatabase()
    projects = project_database.list_projects()
    
    all_merges = []
    for project in projects:
        try:
            repo_name = project.git_url.split('/')[-1].replace('.git', '')
            repo_owner = project.git_url.split('/')[-2]
            
            # Get recent merges
            merges = github_manager.get_recent_merges(
                owner=repo_owner,
                repo=repo_name,
                days=7
            )
            
            # Add project info to merges
            for merge in merges:
                merge['project_name'] = project.name
                merge['project_id'] = project.id
                all_merges.append(merge)
        except Exception as e:
            logger.error(f"Error getting merges for {project.name}: {e}")
    
    # Sort merges by date
    all_merges.sort(key=lambda x: x.get('merged_at', ''), reverse=True)
    
    # Display recent merges
    if all_merges:
        for i, merge in enumerate(all_merges[:5]):  # Show only the 5 most recent merges
            pr_number = merge.get('number')
            title = merge.get('title')
            project_name = merge.get('project_name')
            merged_at = merge.get('merged_at')
            
            st.write(f"**{project_name}:** PR #{pr_number} - {title} (merged {merged_at})")
            
            # Add a separator except for the last item
            if i < len(all_merges[:5]) - 1:
                st.markdown("---")
    else:
        st.info("No recent activity found.")

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
    # Project metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**Repository:** {project.git_url}")
    with col2:
        st.write(f"**Slack Channel:** {project.slack_channel or 'Default'}")
    with col3:
        st.write(f"**Concurrency:** {project.max_parallel_tasks}")
    
    # Three-column layout as per the mockup
    left_col, main_col, right_col = st.columns([1, 2, 1])
    
    with left_col:
        # Step by step structure view
        st.subheader("Step by Step Structure")
        
        # Display the implementation plan steps
        if project.implementation_plan:
            tasks = project.implementation_plan.get('tasks', [])
            for i, task in enumerate(tasks):
                status = "✓" if task.get('status') == 'completed' else " "
                st.write(f"{i+1}. [{status}] {task.get('title')}")
        else:
            st.info("No implementation plan found. Generate a plan to get started.")
    
    with main_col:
        # Project context document view with tabbed interface
        st.subheader("Project Context")
        
        # Create tabs for different document categories
        doc_categories = ["Requirements", "Architecture", "Implementation", "Testing"]
        doc_tabs = st.tabs(doc_categories)
        
        # Render content for each document category
        for i, tab in enumerate(doc_tabs):
            with tab:
                category = doc_categories[i].lower()
                
                # Filter documents by category
                category_docs = [doc for doc in project.documents if f"/{category}/" in doc.lower()]
                
                if category_docs:
                    for doc in category_docs:
                        doc_name = os.path.basename(doc)
                        st.write(f"**{doc_name}**")
                        
                        # Display document content
                        try:
                            with open(doc, 'r') as f:
                                content = f.read()
                                st.text_area("", content, height=300, key=f"doc_{doc}")
                        except Exception as e:
                            st.error(f"Error reading document: {e}")
                else:
                    st.info(f"No {doc_categories[i]} documents found.")
        
        # Concurrency setting
        st.subheader("Concurrency Setting")
        new_concurrency = st.slider(
            "Maximum Concurrent Tasks",
            min_value=1,
            max_value=10,
            value=project.max_parallel_tasks,
            help="Set the maximum number of tasks that can be processed concurrently."
        )
        
        if new_concurrency != project.max_parallel_tasks:
            if st.button("Update Concurrency"):
                project_database = ProjectDatabase()
                project.max_parallel_tasks = new_concurrency
                if project_database.save_project(project):
                    st.success(f"Concurrency updated to {new_concurrency} tasks.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to update concurrency settings.")
        
        # Project settings button
        if st.button("Project Settings"):
            st.session_state.show_settings = True
    
    with right_col:
        # Tree structure view
        st.subheader("Implementation Tree")
        
        # Display the implementation tree
        if project.implementation_plan:
            render_implementation_tree(project.id, compact=True)
        else:
            st.info("No implementation plan found. Generate a plan to get started.")
    
    # Settings dialog
    if st.session_state.get("show_settings", False):
        with st.expander("Project Settings", expanded=True):
            st.write("### Project Settings")
            
            # Slack channel settings
            st.write("#### Slack Integration")
            new_slack_channel = st.text_input(
                "Slack Channel",
                value=project.slack_channel or "",
                help="Set the Slack channel for project notifications."
            )
            
            # GitHub repository settings
            st.write("#### GitHub Integration")
            new_git_url = st.text_input(
                "GitHub Repository URL",
                value=project.git_url,
                help="Set the GitHub repository URL for the project."
            )
            
            # Save settings button
            if st.button("Save Settings"):
                project_database = ProjectDatabase()
                
                # Update project settings
                project.slack_channel = new_slack_channel
                project.git_url = new_git_url
                
                if project_database.save_project(project):
                    st.success("Project settings updated successfully!")
                    st.session_state.show_settings = False
                    st.experimental_rerun()
                else:
                    st.error("Failed to update project settings.")
            
            # Cancel button
            if st.button("Cancel"):
                st.session_state.show_settings = False
                st.experimental_rerun()

# Runtime configuration
def main():
    """Main Streamlit application."""
    # Initialize session state
    initialize_session_state()
    
    # Apply accessibility styles
    apply_accessibility_styles()
    
    # Main layout
    st.title("Projector")
    
    # Dashboard header with Add Project button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("Dashboard")
    with col2:
        if st.button("➕ Add Project", key="add_project_button"):
            st.session_state.show_new_project_form = True
    
    # Show new project form if button was clicked
    if st.session_state.get("show_new_project_form", False):
        with st.expander("Create New Project", expanded=True):
            # Project name
            project_name = st.text_input("Project Name")
            
            # GitHub URL
            github_url = st.text_input("GitHub Repository URL")
            
            # Slack channel
            slack_channel = st.text_input("Slack Channel (optional)")
            
            # Concurrency
            concurrency = st.slider("Maximum Concurrent Tasks", min_value=1, max_value=10, value=2)
            
            # Create project button
            if st.button("Create Project"):
                if project_name and github_url:
                    # Create the project
                    project_database = ProjectDatabase()
                    project_id = project_database.create_project(project_name, github_url, slack_channel)
                    
                    if project_id:
                        # Update the project's concurrency
                        project = project_database.get_project(project_id)
                        project.max_parallel_tasks = concurrency
                        project_database.save_project(project)
                        
                        st.success(f"Project '{project_name}' created successfully!")
                        st.session_state.show_new_project_form = False
                        st.experimental_rerun()
                    else:
                        st.error("Failed to create project.")
                else:
                    st.error("Project name and GitHub URL are required.")
            
            # Cancel button
            if st.button("Cancel"):
                st.session_state.show_new_project_form = False
                st.experimental_rerun()
    
    # Recent activity dashboard
    st.subheader("Recent Activity")
    render_recent_activity()
    
    # Render multi-project tabs
    render_multi_project_tabs()
    
    # Render chat interface at the bottom
    st.write("---")
    render_chat_interface(
        project_id=st.session_state.get("selected_project")
    )
    
    # Update session data
    update_session_data()

if __name__ == "__main__":
    main()
