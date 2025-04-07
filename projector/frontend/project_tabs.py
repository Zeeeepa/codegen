"""
Tabbed interface component for the Projector system.
"""
import streamlit as st
import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend components
from projector.backend.project_database import ProjectDatabase

def render_tabbed_interface(projects):
    """Render a tabbed interface for projects with closable tabs.
    
    Args:
        projects: List of Project objects
    """
    if not projects:
        st.info("No projects found. Create a new project to get started.")
        return
    
    # Get the currently selected project ID
    selected_project_id = st.session_state.get("selected_project")
    
    # Create a list of project names for tabs
    project_names = []
    for project in projects:
        # Add an "X" to the tab name for closable tabs
        project_names.append(f"{project.name}|[X]")
    
    # Create tabs
    tab_indices = range(len(projects))
    tabs = st.tabs(project_names)
    
    # Render content for each tab
    for i, tab in enumerate(tabs):
        with tab:
            project = projects[i]
            
            # Set the selected project when a tab is clicked
            if selected_project_id != project.id:
                st.session_state.selected_project = project.id
            
            # Render project content
            st.subheader(f"Project: {project.name}")
            
            # Project context document view
            st.write("Project's context document view")
            
            # Display documents if available
            if project.documents:
                for doc in project.documents:
                    st.write(f"- {os.path.basename(doc)}")
            else:
                st.info("No documents uploaded yet. Upload documents to get started.")
            
            # Concurrency setting
            col1, col2 = st.columns([3, 1])
            
            with col1:
                concurrency = st.number_input(
                    "Concurrency",
                    min_value=1,
                    max_value=10,
                    value=project.max_parallel_tasks,
                    help="Set the maximum number of concurrent feature lifecycles"
                )
                
                if concurrency != project.max_parallel_tasks:
                    project.max_parallel_tasks = concurrency
                    project_database = ProjectDatabase()
                    project_database.save_project(project)
            
            with col2:
                if st.button("Project Settings", key=f"settings_{project.id}"):
                    st.session_state[f"show_settings_{project.id}"] = True
            
            # Project settings dialog
            if st.session_state.get(f"show_settings_{project.id}", False):
                with st.expander("Project Settings", expanded=True):
                    # GitHub URL
                    github_url = st.text_input(
                        "GitHub Repository URL",
                        value=project.git_url,
                        key=f"github_url_{project.id}"
                    )
                    
                    # Slack channel
                    slack_channel = st.text_input(
                        "Slack Channel ID (optional)",
                        value=project.slack_channel or "",
                        key=f"slack_channel_{project.id}"
                    )
                    
                    # Save settings
                    if st.button("Save", key=f"save_settings_{project.id}"):
                        project.git_url = github_url
                        project.slack_channel = slack_channel
                        
                        project_database = ProjectDatabase()
                        if project_database.save_project(project):
                            st.success("Settings saved successfully!")
                            st.session_state[f"show_settings_{project.id}"] = False
                            st.experimental_rerun()
                        else:
                            st.error("Failed to save settings.")
                    
                    # Cancel button
                    if st.button("Cancel", key=f"cancel_settings_{project.id}"):
                        st.session_state[f"show_settings_{project.id}"] = False
                        st.experimental_rerun()
            
            # Initialize project button
            if st.button("Initialize", key=f"initialize_{project.id}"):
                st.session_state[f"initializing_{project.id}"] = True
                st.info("Initializing project... This may take a few moments.")
                
                # TODO: Implement actual initialization with LLM processing
                # This would involve:
                # 1. Processing documents with LLM
                # 2. Creating high-level structural tree
                # 3. Creating step-by-step action list
                
                # For now, we'll just simulate it
                import time
                time.sleep(2)
                
                # Create a sample implementation plan
                project.implementation_plan = {
                    "tasks": [
                        {
                            "id": "task1",
                            "title": "Setup project structure",
                            "description": "Create the basic project structure and configuration files",
                            "status": "completed",
                            "subtasks": []
                        },
                        {
                            "id": "task2",
                            "title": "Implement core functionality",
                            "description": "Implement the core functionality of the project",
                            "status": "in_progress",
                            "subtasks": [
                                {
                                    "id": "subtask1",
                                    "title": "Create data models",
                                    "status": "completed"
                                },
                                {
                                    "id": "subtask2",
                                    "title": "Implement business logic",
                                    "status": "in_progress"
                                }
                            ]
                        },
                        {
                            "id": "task3",
                            "title": "Create user interface",
                            "description": "Design and implement the user interface",
                            "status": "not_started",
                            "subtasks": []
                        }
                    ]
                }
                
                # Save the project with the implementation plan
                project_database = ProjectDatabase()
                project_database.save_project(project)
                
                st.success("Project initialized successfully!")
                st.session_state[f"initializing_{project.id}"] = False
                st.experimental_rerun()
            
            # Close tab button
            if st.button("Close Tab", key=f"close_{project.id}"):
                # Remove the project from the session state
                if st.session_state.get("selected_project") == project.id:
                    st.session_state.selected_project = None
                
                # Refresh the page to update the tabs
                st.experimental_rerun()

def render_step_by_step_view(project):
    """Render a step-by-step view of the project implementation plan.
    
    Args:
        project: Project object
    """
    if not project.implementation_plan:
        st.info("No implementation plan found. Initialize the project to generate a plan.")
        return
    
    # Get tasks from the implementation plan
    tasks = project.implementation_plan.get('tasks', [])
    
    if not tasks:
        st.info("No tasks found in the implementation plan.")
        return
    
    # Display tasks in a step-by-step format
    for i, task in enumerate(tasks):
        status = "✓" if task.get('status') == 'completed' else " "
        st.write(f"{i+1}. [{status}] {task.get('title')}")
        
        # Display subtasks if any
        subtasks = task.get('subtasks', [])
        for j, subtask in enumerate(subtasks):
            status = "✓" if subtask.get('status') == 'completed' else " "
            st.write(f"   {i+1}.{j+1}. [{status}] {subtask.get('title')}")
