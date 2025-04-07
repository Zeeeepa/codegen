"""
Resource Management UI components for the Projector system.
This module provides UI components for managing team members, skills, and resource allocation.
"""
import streamlit as st
import os
import sys
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import backend components
from projector.backend.project_database import ProjectDatabase
from projector.backend.project_manager import ProjectManager

def render_team_management():
    """Render the team management interface."""
    st.header("Team Management")
    
    # Team members data (in a real implementation, this would come from a database)
    if 'team_members' not in st.session_state:
        st.session_state.team_members = [
            {
                "id": "1",
                "name": "Alex Johnson",
                "role": "Full Stack Developer",
                "skills": ["Python", "React", "Node.js", "MongoDB"],
                "availability": 0.8,
                "avatar": "👨‍💻"
            },
            {
                "id": "2",
                "name": "Sarah Chen",
                "role": "UX Designer",
                "skills": ["UI Design", "User Research", "Figma", "Prototyping"],
                "availability": 0.6,
                "avatar": "👩‍🎨"
            },
            {
                "id": "3",
                "name": "Michael Rodriguez",
                "role": "Backend Developer",
                "skills": ["Python", "Django", "PostgreSQL", "Docker"],
                "availability": 0.9,
                "avatar": "👨‍💻"
            },
            {
                "id": "4",
                "name": "Emma Wilson",
                "role": "Project Manager",
                "skills": ["Agile", "Scrum", "Risk Management", "Stakeholder Communication"],
                "availability": 0.7,
                "avatar": "👩‍💼"
            }
        ]
    
    # Display team members in a table
    team_data = []
    for member in st.session_state.team_members:
        team_data.append({
            "ID": member["id"],
            "Name": member["name"],
            "Role": member["role"],
            "Skills": ", ".join(member["skills"]),
            "Availability": f"{int(member['availability'] * 100)}%",
            "Avatar": member["avatar"]
        })
    
    team_df = pd.DataFrame(team_data)
    st.dataframe(team_df)
    
    # Add new team member
    with st.expander("Add New Team Member"):
        with st.form("add_team_member_form"):
            name = st.text_input("Name")
            role = st.text_input("Role")
            skills = st.text_input("Skills (comma-separated)")
            availability = st.slider("Availability (%)", 0, 100, 80) / 100
            avatar_options = ["👨‍💻", "👩‍💻", "👨‍🎨", "👩‍🎨", "👨‍💼", "👩‍💼", "🧑‍💻", "🧑‍🎨", "🧑‍💼"]
            avatar = st.selectbox("Avatar", avatar_options)
            
            submitted = st.form_submit_button("Add Team Member")
            
            if submitted:
                if name and role:
                    # Generate a new ID (in a real implementation, this would be handled by the database)
                    new_id = str(len(st.session_state.team_members) + 1)
                    
                    # Add the new team member
                    st.session_state.team_members.append({
                        "id": new_id,
                        "name": name,
                        "role": role,
                        "skills": [skill.strip() for skill in skills.split(",") if skill.strip()],
                        "availability": availability,
                        "avatar": avatar
                    })
                    
                    st.success(f"Team member '{name}' added successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Name and role are required.")

def render_skill_matrix():
    """Render the skill matrix visualization."""
    st.header("Skill Matrix")
    
    if 'team_members' not in st.session_state or not st.session_state.team_members:
        st.info("No team members found. Add team members to view the skill matrix.")
        return
    
    # Extract all unique skills
    all_skills = set()
    for member in st.session_state.team_members:
        all_skills.update(member["skills"])
    
    # Create skill matrix data
    skill_data = []
    for member in st.session_state.team_members:
        for skill in all_skills:
            skill_level = random.randint(1, 5) if skill in member["skills"] else 0
            skill_data.append({
                "Team Member": member["name"],
                "Skill": skill,
                "Level": skill_level
            })
    
    # Create heatmap
    skill_df = pd.DataFrame(skill_data)
    fig = px.density_heatmap(
        skill_df,
        x="Skill",
        y="Team Member",
        z="Level",
        title="Team Skill Matrix",
        color_continuous_scale="Viridis",
        range_color=[0, 5]
    )
    
    fig.update_layout(
        xaxis_title="Skill",
        yaxis_title="Team Member",
        coloraxis_colorbar=dict(
            title="Skill Level",
            tickvals=[0, 1, 2, 3, 4, 5],
            ticktext=["None", "Basic", "Intermediate", "Advanced", "Expert", "Master"]
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Skill gap analysis
    st.subheader("Skill Gap Analysis")
    
    # Calculate skill coverage
    skill_coverage = {}
    for skill in all_skills:
        members_with_skill = sum(1 for member in st.session_state.team_members if skill in member["skills"])
        coverage_percentage = (members_with_skill / len(st.session_state.team_members)) * 100
        skill_coverage[skill] = coverage_percentage
    
    # Create bar chart
    coverage_df = pd.DataFrame({
        "Skill": list(skill_coverage.keys()),
        "Coverage (%)": list(skill_coverage.values())
    })
    
    fig = px.bar(
        coverage_df,
        x="Skill",
        y="Coverage (%)",
        title="Skill Coverage",
        color="Coverage (%)",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100]
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_resource_allocation():
    """Render the resource allocation interface."""
    st.header("Resource Allocation")
    
    if 'team_members' not in st.session_state or not st.session_state.team_members:
        st.info("No team members found. Add team members to allocate resources.")
        return
    
    # Get the selected project
    if "selected_project" not in st.session_state:
        st.warning("Please select a project first.")
        return
    
    project_id = st.session_state.selected_project
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    st.subheader(f"Resource Allocation for: {project.name}")
    
    # Check if the project has an implementation plan
    implementation_plan = getattr(project, 'implementation_plan', None)
    
    if not implementation_plan:
        st.info("No implementation plan found. Generate a plan to allocate resources.")
        return
    
    # Get tasks
    tasks = implementation_plan.get('tasks', [])
    
    if not tasks:
        st.info("No tasks found in the implementation plan.")
        return
    
    # Create task allocation interface
    st.subheader("Task Assignments")
    
    # Initialize task assignments if not already in session state
    if 'task_assignments' not in st.session_state:
        st.session_state.task_assignments = {}
    
    # Display task assignments
    for task in tasks:
        task_id = task.get('id', 'N/A')
        task_title = task.get('title', 'Unknown Task')
        task_status = task.get('status', 'pending')
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{task_title}** (Status: {task_status})")
        
        with col2:
            # Get the current assignee for this task
            current_assignee = st.session_state.task_assignments.get(task_id, "Unassigned")
            
            # Create a dropdown to select an assignee
            team_options = ["Unassigned"] + [member["name"] for member in st.session_state.team_members]
            selected_assignee = st.selectbox(
                "Assignee",
                team_options,
                index=team_options.index(current_assignee) if current_assignee in team_options else 0,
                key=f"assignee_{task_id}"
            )
            
            # Update the assignment if changed
            if selected_assignee != current_assignee:
                st.session_state.task_assignments[task_id] = selected_assignee
    
    # Display resource allocation visualization
    st.subheader("Resource Allocation Overview")
    
    # Calculate workload per team member
    workload = {}
    for member in st.session_state.team_members:
        workload[member["name"]] = 0
    
    # Count tasks assigned to each team member
    for task_id, assignee in st.session_state.task_assignments.items():
        if assignee != "Unassigned" and assignee in workload:
            workload[assignee] += 1
    
    # Create bar chart
    workload_df = pd.DataFrame({
        "Team Member": list(workload.keys()),
        "Assigned Tasks": list(workload.values())
    })
    
    fig = px.bar(
        workload_df,
        x="Team Member",
        y="Assigned Tasks",
        title="Task Distribution",
        color="Assigned Tasks",
        color_continuous_scale="Blues"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display workload vs. availability
    st.subheader("Workload vs. Availability")
    
    # Calculate workload percentage (assuming each task takes 20% of capacity)
    workload_percentage = {}
    for member in st.session_state.team_members:
        tasks_assigned = workload.get(member["name"], 0)
        workload_percentage[member["name"]] = min(tasks_assigned * 20, 100)
    
    # Create comparison data
    comparison_data = []
    for member in st.session_state.team_members:
        comparison_data.append({
            "Team Member": member["name"],
            "Metric": "Availability",
            "Value": member["availability"] * 100
        })
        comparison_data.append({
            "Team Member": member["name"],
            "Metric": "Workload",
            "Value": workload_percentage.get(member["name"], 0)
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    fig = px.bar(
        comparison_df,
        x="Team Member",
        y="Value",
        color="Metric",
        barmode="group",
        title="Workload vs. Availability (%)",
        color_discrete_map={
            "Availability": "#00CC96",
            "Workload": "#636EFA"
        }
    )
    
    fig.update_layout(yaxis_title="Percentage (%)")
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Overallocation warnings
    for member in st.session_state.team_members:
        member_name = member["name"]
        availability = member["availability"] * 100
        current_workload = workload_percentage.get(member_name, 0)
        
        if current_workload > availability:
            st.warning(f"⚠️ {member_name} is overallocated! Workload: {current_workload}%, Availability: {availability}%")

def render_resource_timeline():
    """Render the resource timeline visualization."""
    st.header("Resource Timeline")
    
    if 'team_members' not in st.session_state or not st.session_state.team_members:
        st.info("No team members found. Add team members to view the resource timeline.")
        return
    
    # Get the selected project
    if "selected_project" not in st.session_state:
        st.warning("Please select a project first.")
        return
    
    project_id = st.session_state.selected_project
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    # Check if the project has an implementation plan
    implementation_plan = getattr(project, 'implementation_plan', None)
    
    if not implementation_plan:
        st.info("No implementation plan found. Generate a plan to view the timeline.")
        return
    
    # Get tasks
    tasks = implementation_plan.get('tasks', [])
    
    if not tasks:
        st.info("No tasks found in the implementation plan.")
        return
    
    # Create timeline data (in a real implementation, this would use actual task dates)
    today = datetime.now().date()
    timeline_data = []
    
    for task in tasks:
        task_id = task.get('id', 'N/A')
        task_title = task.get('title', 'Unknown Task')
        task_status = task.get('status', 'pending')
        
        # Get the assignee for this task
        assignee = st.session_state.task_assignments.get(task_id, "Unassigned")
        
        # Generate random start and end dates for demonstration
        if task_status == 'completed':
            start_date = today - timedelta(days=random.randint(30, 60))
            end_date = today - timedelta(days=random.randint(1, 29))
        elif task_status == 'in_progress':
            start_date = today - timedelta(days=random.randint(1, 30))
            end_date = today + timedelta(days=random.randint(1, 30))
        else:
            start_date = today + timedelta(days=random.randint(1, 30))
            end_date = today + timedelta(days=random.randint(31, 90))
        
        timeline_data.append({
            "Task": task_title,
            "Assignee": assignee,
            "Start": start_date,
            "End": end_date,
            "Status": task_status
        })
    
    # Create timeline chart
    if timeline_data:
        df = pd.DataFrame(timeline_data)
        
        # Filter by assignee
        team_options = ["All"] + [member["name"] for member in st.session_state.team_members]
        selected_assignee = st.selectbox("Filter by Team Member", team_options)
        
        if selected_assignee != "All":
            df = df[df["Assignee"] == selected_assignee]
        
        if not df.empty:
            fig = px.timeline(
                df,
                x_start="Start",
                x_end="End",
                y="Task",
                color="Status",
                hover_data=["Assignee"],
                title="Project Timeline",
                color_discrete_map={
                    "completed": "#00CC96",
                    "in_progress": "#FFA15A",
                    "pending": "#636EFA"
                }
            )
            
            fig.update_yaxes(autorange="reversed")
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No tasks assigned to {selected_assignee}.")
    else:
        st.info("No timeline data available.")

def render_resource_management_ui():
    """Render the main resource management UI."""
    st.title("Resource Management")
    
    # Sidebar navigation
    st.sidebar.title("Resource Management")
    page = st.sidebar.radio(
        "Select Page",
        ["Team Management", "Skill Matrix", "Resource Allocation", "Resource Timeline"]
    )
    
    # Render the selected page
    if page == "Team Management":
        render_team_management()
    elif page == "Skill Matrix":
        render_skill_matrix()
    elif page == "Resource Allocation":
        render_resource_allocation()
    elif page == "Resource Timeline":
        render_resource_timeline()

if __name__ == "__main__":
    render_resource_management_ui()