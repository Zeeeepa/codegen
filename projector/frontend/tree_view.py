"""
Implementation tree view component for the Projector system.
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

def render_implementation_tree(project_id, compact=False):
    """Render the implementation tree for a project.
    
    Args:
        project_id: The ID of the project to render the tree for.
        compact: Whether to render a compact version of the tree.
    """
    project_database = ProjectDatabase()
    project = project_database.get_project(project_id)
    
    if not project:
        st.error("Project not found.")
        return
    
    if not project.implementation_plan:
        st.info("No implementation plan found. Generate a plan to get started.")
        return
    
    # Get tasks from the implementation plan
    tasks = project.implementation_plan.get('tasks', [])
    
    if not tasks:
        st.info("No tasks found in the implementation plan.")
        return
    
    # Calculate progress
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
    in_progress_tasks = len([t for t in tasks if t.get('status') == 'in_progress'])
    pending_tasks = total_tasks - completed_tasks - in_progress_tasks
    
    progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Display progress bar
    if not compact:
        st.write(f"**Overall Progress:** {progress_percentage:.1f}%")
        st.progress(progress_percentage / 100)
    
    # Build task hierarchy
    task_hierarchy = build_task_hierarchy(tasks)
    
    # Render the tree
    render_tree_node(task_hierarchy, project_id, project_database, compact=compact)

def build_task_hierarchy(tasks):
    """Build a hierarchical structure from flat tasks list.
    
    Args:
        tasks: List of tasks from the implementation plan.
        
    Returns:
        A dictionary representing the task hierarchy.
    """
    # Create a dictionary to store the hierarchy
    hierarchy = {
        "name": "Root",
        "children": [],
        "tasks": {}
    }
    
    # First pass: add all tasks to the hierarchy
    for task in tasks:
        task_id = task.get('id')
        hierarchy["tasks"][task_id] = task
    
    # Second pass: build the hierarchy based on dependencies
    for task in tasks:
        task_id = task.get('id')
        dependencies = task.get('dependencies', [])
        
        if not dependencies:
            # This is a root-level task
            hierarchy["children"].append({
                "id": task_id,
                "children": []
            })
        else:
            # Find the parent task and add this task as a child
            for dep_id in dependencies:
                # Find the node that contains this dependency
                add_child_to_parent(hierarchy, dep_id, {
                    "id": task_id,
                    "children": []
                })
    
    return hierarchy

def add_child_to_parent(node, parent_id, child):
    """Add a child node to its parent in the hierarchy.
    
    Args:
        node: The current node in the hierarchy.
        parent_id: The ID of the parent task.
        child: The child node to add.
    
    Returns:
        True if the child was added, False otherwise.
    """
    # Check if this node is the parent
    if node.get("id") == parent_id:
        node["children"].append(child)
        return True
    
    # Check children
    for child_node in node.get("children", []):
        if add_child_to_parent(child_node, parent_id, child):
            return True
    
    return False

def render_tree_node(node, project_id, project_database, level=0, prefix="", compact=False):
    """Render a node in the implementation tree.
    
    Args:
        node: The node to render.
        project_id: The ID of the project.
        project_database: The project database.
        level: The current level in the tree.
        prefix: The prefix to use for the current line.
        compact: Whether to render a compact version of the tree.
    """
    # Skip the root node
    if level == 0:
        # Render children of the root node
        for i, child in enumerate(node.get("children", [])):
            is_last = i == len(node.get("children", [])) - 1
            child_prefix = "└── " if is_last else "├── "
            child_continuation = "    " if is_last else "│   "
            render_tree_node(
                child, 
                project_id, 
                project_database, 
                level + 1, 
                child_prefix, 
                compact
            )
        return
    
    # Get the task
    task_id = node.get("id")
    task = node.get("tasks", {}).get(task_id) if "tasks" in node else None
    
    if not task and "tasks" in node.get("parent", {}):
        task = node.get("parent", {}).get("tasks", {}).get(task_id)
    
    if not task:
        # Try to get the task from the project database
        project = project_database.get_project(project_id)
        if project and project.implementation_plan:
            tasks = project.implementation_plan.get('tasks', [])
            task = next((t for t in tasks if t.get('id') == task_id), None)
    
    if not task:
        return
    
    # Get task details
    title = task.get('title', 'Unknown Task')
    status = task.get('status', 'pending')
    
    # Determine the checkbox state
    is_completed = status == 'completed'
    checkbox_str = "[✓]" if is_completed else "[ ]"
    
    # Render the task
    if compact:
        # Compact version
        st.write(f"{prefix}{title} {checkbox_str}")
    else:
        # Full version with interactive checkbox
        col1, col2 = st.columns([9, 1])
        with col1:
            st.write(f"{prefix}{title}")
        with col2:
            new_status = st.checkbox(
                "",
                value=is_completed,
                key=f"task_{task_id}",
                help=f"Mark task '{title}' as {'incomplete' if is_completed else 'complete'}"
            )
            
            # Update task status if changed
            if new_status != is_completed:
                update_task_status(
                    task_id,
                    "completed" if new_status else "pending",
                    project_id,
                    project_database
                )
                st.experimental_rerun()
    
    # Render children
    for i, child in enumerate(node.get("children", [])):
        is_last = i == len(node.get("children", [])) - 1
        child_prefix = prefix + ("└── " if is_last else "├── ")
        child_continuation = prefix + ("    " if is_last else "│   ")
        
        # Pass the tasks dictionary to the child
        if "tasks" in node:
            child["parent"] = {"tasks": node["tasks"]}
        
        render_tree_node(
            child, 
            project_id, 
            project_database, 
            level + 1, 
            child_prefix, 
            compact
        )

def update_task_status(task_id, status, project_id, project_database):
    """Update the status of a task.
    
    Args:
        task_id: The ID of the task to update.
        status: The new status of the task.
        project_id: The ID of the project.
        project_database: The project database.
    
    Returns:
        True if the task was updated, False otherwise.
    """
    project = project_database.get_project(project_id)
    
    if not project or not project.implementation_plan:
        return False
    
    # Update the task status
    tasks = project.implementation_plan.get('tasks', [])
    for task in tasks:
        if task['id'] == task_id:
            task['status'] = status
            if status == 'completed':
                task['completed_at'] = datetime.now().timestamp()
            break
    
    # Save the updated project
    project.implementation_plan['tasks'] = tasks
    return project_database.save_project(project)