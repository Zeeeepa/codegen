"""
Project UI components for the Projector system.
"""
import streamlit as st
import os
import sys
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend components
from projector.backend.project_database import ProjectDatabase
from projector.backend.project_manager import ProjectManager
from projector.backend.ai_user_agent import AIUserAgent

def render_project_creation_form():
    """Render the project creation form."""
    st.header("Create New Project")
    
    with st.form("create_project_form"):
        project_name = st.text_input("Project Name")
        git_url = st.text_input("GitHub Repository URL")
        slack_channel = st.text_input("Slack Channel (optional)")
        
        submitted = st.form_submit_button("Create Project")
        
        if submitted:
            if not project_name or not git_url:
                st.error("Project name and GitHub URL are required.")
                return
            
            # Create the project
            project_database = ProjectDatabase()
            project_id = project_database.create_project(project_name, git_url, slack_channel)
            
            if project_id:
                st.success(f"Project '{project_name}' created successfully!")
                st.session_state.selected_project = project_id
                st.experimental_rerun()
            else:
                st.error("Failed to create project. Please try again.")

def render_document_upload():
    """Render the document upload form."""
    st.header("Upload Project Documents")
    
    if "selected_project" not in st.session_state:
        st.warning("Please select a project first.")
        return
    
    project_id = st.session_state.selected_project
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    st.subheader(f"Upload Documents for: {project.name}")
    
    uploaded_file = st.file_uploader("Upload Markdown Document", type=["md"])
    
    if uploaded_file:
        # Save the uploaded file
        docs_dir = os.path.join("docs", project.name)
        os.makedirs(docs_dir, exist_ok=True)
        
        file_path = os.path.join(docs_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Add the document to the project
        if project_database.add_document_to_project(project_id, file_path):
            st.success(f"Document '{uploaded_file.name}' uploaded successfully!")
        else:
            st.error("Failed to add document to project.")

def render_project_list():
    """Render the list of projects."""
    st.header("Projects")
    
    project_database = ProjectDatabase()
    projects = project_database.list_projects()
    
    if not projects:
        st.info("No projects found. Create a new project to get started.")
        return
    
    # Create a DataFrame for display
    project_data = []
    for project in projects:
        project_data.append({
            "ID": project.id,
            "Name": project.name,
            "Repository": project.git_url,
            "Slack Channel": project.slack_channel or "Default",
            "Documents": len(project.documents),
            "Created": project.created_at
        })
    
    df = pd.DataFrame(project_data)
    
    # Display the projects
    st.dataframe(df)
    
    # Project selection
    project_names = [p.name for p in projects]
    selected_project_name = st.selectbox("Select Project", project_names)
    
    if selected_project_name:
        selected_project = next((p for p in projects if p.name == selected_project_name), None)
        if selected_project:
            st.session_state.selected_project = selected_project.id
            st.success(f"Project '{selected_project_name}' selected.")

def render_implementation_plan():
    """Render the implementation plan for the selected project."""
    st.header("Implementation Plan")
    
    if "selected_project" not in st.session_state:
        st.warning("Please select a project first.")
        return
    
    project_id = st.session_state.selected_project
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    st.subheader(f"Implementation Plan for: {project.name}")
    
    # Check if the project has an implementation plan
    implementation_plan = getattr(project, 'implementation_plan', None)
    
    if not implementation_plan:
        st.info("No implementation plan found. Generate a plan to get started.")
        
        if st.button("Generate Implementation Plan"):
            # Initialize AI User Agent
            from projector.backend.slack_manager import SlackManager
            from projector.backend.github_manager import GitHubManager
            from projector.backend.thread_pool import ThreadPool
            from projector.backend.project_manager import ProjectManager
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
                implementation_plan = ai_user_agent.create_implementation_plan(project_id)
                
                if implementation_plan:
                    st.success("Implementation plan generated successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to generate implementation plan.")
        
        return
    
    # Display the implementation plan
    st.subheader("Plan Overview")
    
    # Display plan metadata
    st.write(f"**Plan ID:** {implementation_plan.get('id', 'N/A')}")
    st.write(f"**Created:** {implementation_plan.get('created_at', 'N/A')}")
    st.write(f"**Description:** {implementation_plan.get('description', 'N/A')}")
    
    # Display tasks
    st.subheader("Tasks")
    
    tasks = implementation_plan.get('tasks', [])
    
    if not tasks:
        st.info("No tasks found in the implementation plan.")
        return
    
    # Create a DataFrame for display
    task_data = []
    for task in tasks:
        task_data.append({
            "ID": task.get('id', 'N/A'),
            "Title": task.get('title', 'N/A'),
            "Status": task.get('status', 'pending'),
            "Dependencies": ", ".join(task.get('dependencies', [])),
            "Priority": task.get('priority', 'medium')
        })
    
    df = pd.DataFrame(task_data)
    
    # Display the tasks
    st.dataframe(df)
    
    # Display task details
    st.subheader("Task Details")
    
    task_ids = [t.get('id', 'N/A') for t in tasks]
    selected_task_id = st.selectbox("Select Task", task_ids)
    
    if selected_task_id:
        selected_task = next((t for t in tasks if t.get('id') == selected_task_id), None)
        if selected_task:
            st.write(f"**Title:** {selected_task.get('title', 'N/A')}")
            st.write(f"**Description:** {selected_task.get('description', 'N/A')}")
            st.write(f"**Status:** {selected_task.get('status', 'pending')}")
            st.write(f"**Priority:** {selected_task.get('priority', 'medium')}")
            
            # Display requirements
            st.write("**Requirements:**")
            for req in selected_task.get('requirements', []):
                st.write(f"- {req}")
            
            # Display dependencies
            st.write("**Dependencies:**")
            for dep in selected_task.get('dependencies', []):
                st.write(f"- {dep}")
            
            # Display implementation details
            if selected_task.get('implementation_details'):
                st.write("**Implementation Details:**")
                st.code(selected_task.get('implementation_details'))
            
            # Implementation actions
            st.subheader("Implementation Actions")
            
            if st.button("Send Implementation Request"):
                # Initialize AI User Agent
                from projector.backend.slack_manager import SlackManager
                from projector.backend.github_manager import GitHubManager
                from projector.backend.thread_pool import ThreadPool
                from projector.backend.project_manager import ProjectManager
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
                
                ai_user_agent = AIUserAgent(
                    slack_manager=slack_manager,
                    github_manager=github_manager,
                    project_database=project_database,
                    project_manager=project_manager,
                    thread_pool=thread_pool,
                    docs_path="docs"
                )
                
                # Send the implementation request
                with st.spinner("Sending implementation request..."):
                    success = ai_user_agent.send_implementation_request(project_id, selected_task_id)
                    
                    if success:
                        st.success("Implementation request sent successfully!")
                    else:
                        st.error("Failed to send implementation request.")

def render_project_progress():
    """Render the progress of the selected project."""
    st.header("Project Progress")
    
    if "selected_project" not in st.session_state:
        st.warning("Please select a project first.")
        return
    
    project_id = st.session_state.selected_project
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    st.subheader(f"Progress for: {project.name}")
    
    # Check if the project has an implementation plan
    implementation_plan = getattr(project, 'implementation_plan', None)
    
    if not implementation_plan:
        st.info("No implementation plan found. Generate a plan to track progress.")
        return
    
    # Get tasks
    tasks = implementation_plan.get('tasks', [])
    
    if not tasks:
        st.info("No tasks found in the implementation plan.")
        return
    
    # Calculate progress
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
    in_progress_tasks = len([t for t in tasks if t.get('status') == 'in_progress'])
    pending_tasks = total_tasks - completed_tasks - in_progress_tasks
    
    progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Display progress metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tasks", total_tasks)
    
    with col2:
        st.metric("Completed", completed_tasks)
    
    with col3:
        st.metric("In Progress", in_progress_tasks)
    
    with col4:
        st.metric("Pending", pending_tasks)
    
    # Display progress bar
    st.progress(progress_percentage / 100)
    st.write(f"Overall Progress: {progress_percentage:.1f}%")
    
    # Display progress chart
    progress_data = {
        "Status": ["Completed", "In Progress", "Pending"],
        "Count": [completed_tasks, in_progress_tasks, pending_tasks]
    }
    
    fig = px.pie(
        progress_data,
        names="Status",
        values="Count",
        title="Task Status Distribution",
        color="Status",
        color_discrete_map={
            "Completed": "#00CC96",
            "In Progress": "#FFA15A",
            "Pending": "#636EFA"
        }
    )
    
    st.plotly_chart(fig)
    
    # Display task status timeline
    st.subheader("Task Status Timeline")
    
    # Create timeline data
    timeline_data = []
    for task in tasks:
        status = task.get('status', 'pending')
        started_at = task.get('started_at', None)
        completed_at = task.get('completed_at', None)
        
        if status == 'completed' and started_at and completed_at:
            timeline_data.append({
                "Task": task.get('title', 'Unknown'),
                "Start": datetime.fromtimestamp(started_at),
                "Finish": datetime.fromtimestamp(completed_at),
                "Status": status
            })
        elif status == 'in_progress' and started_at:
            timeline_data.append({
                "Task": task.get('title', 'Unknown'),
                "Start": datetime.fromtimestamp(started_at),
                "Finish": datetime.now(),
                "Status": status
            })
    
    if timeline_data:
        df = pd.DataFrame(timeline_data)
        
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Status",
            title="Task Timeline",
            color_discrete_map={
                "completed": "#00CC96",
                "in_progress": "#FFA15A"
            }
        )
        
        st.plotly_chart(fig)
    else:
        st.info("No timeline data available yet.")
    
    # Refresh button
    if st.button("Refresh Progress"):
        # Initialize AI User Agent
        from projector.backend.slack_manager import SlackManager
        from projector.backend.github_manager import GitHubManager
        from projector.backend.thread_pool import ThreadPool
        from projector.backend.project_manager import ProjectManager
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
        
        ai_user_agent = AIUserAgent(
            slack_manager=slack_manager,
            github_manager=github_manager,
            project_database=project_database,
            project_manager=project_manager,
            thread_pool=thread_pool,
            docs_path="docs"
        )
        
        # Monitor project progress
        with st.spinner("Refreshing project progress..."):
            progress = ai_user_agent.monitor_project_progress(project_id)
            
            if progress:
                st.success("Project progress refreshed successfully!")
                st.experimental_rerun()
            else:
                st.error("Failed to refresh project progress.")

def render_project_ui():
    """Render the main project UI."""
    st.title("Projector: AI-Powered Project Management")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Projects", "Create Project", "Upload Documents", "Implementation Plan", "Project Progress"]
    )
    
    # Render the selected page
    if page == "Projects":
        render_project_list()
    elif page == "Create Project":
        render_project_creation_form()
    elif page == "Upload Documents":
        render_document_upload()
    elif page == "Implementation Plan":
        render_implementation_plan()
    elif page == "Project Progress":
        render_project_progress()

if __name__ == "__main__":
    render_project_ui()