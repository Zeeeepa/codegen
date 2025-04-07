"""
API routes for project management.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from datetime import datetime

from projector.backend.project_database import ProjectDatabase
from projector.backend.project import Project
from projector.api.models.project import ProjectCreate, ProjectUpdate, Project as ProjectModel
from projector.api.main import get_project_database, get_project_manager, get_ai_user_agent

router = APIRouter()

@router.get("/", response_model=List[ProjectModel])
async def list_projects(
    project_database: ProjectDatabase = Depends(get_project_database)
):
    """List all projects."""
    projects = project_database.list_projects()
    return [
        ProjectModel(
            id=project.id,
            name=project.name,
            git_url=project.git_url,
            slack_channel=project.slack_channel,
            max_parallel_tasks=project.max_parallel_tasks,
            documents=project.documents,
            features=project.features,
            implementation_plan=project.implementation_plan,
            created_at=datetime.fromisoformat(project.created_at),
            updated_at=datetime.fromisoformat(project.updated_at)
        )
        for project in projects
    ]

@router.get("/{project_id}", response_model=ProjectModel)
async def get_project(
    project_id: str,
    project_database: ProjectDatabase = Depends(get_project_database)
):
    """Get a project by ID."""
    project = project_database.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectModel(
        id=project.id,
        name=project.name,
        git_url=project.git_url,
        slack_channel=project.slack_channel,
        max_parallel_tasks=project.max_parallel_tasks,
        documents=project.documents,
        features=project.features,
        implementation_plan=project.implementation_plan,
        created_at=datetime.fromisoformat(project.created_at),
        updated_at=datetime.fromisoformat(project.updated_at)
    )

@router.post("/", response_model=ProjectModel)
async def create_project(
    project_data: ProjectCreate,
    project_database: ProjectDatabase = Depends(get_project_database)
):
    """Create a new project."""
    project_id = project_database.create_project(
        name=project_data.name,
        git_url=project_data.git_url,
        slack_channel=project_data.slack_channel
    )
    
    if not project_id:
        raise HTTPException(status_code=500, detail="Failed to create project")
    
    project = project_database.get_project(project_id)
    project.max_parallel_tasks = project_data.max_parallel_tasks
    project_database.save_project(project)
    
    return ProjectModel(
        id=project.id,
        name=project.name,
        git_url=project.git_url,
        slack_channel=project.slack_channel,
        max_parallel_tasks=project.max_parallel_tasks,
        documents=project.documents,
        features=project.features,
        implementation_plan=project.implementation_plan,
        created_at=datetime.fromisoformat(project.created_at),
        updated_at=datetime.fromisoformat(project.updated_at)
    )

@router.put("/{project_id}", response_model=ProjectModel)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    project_database: ProjectDatabase = Depends(get_project_database)
):
    """Update a project."""
    project = project_database.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update project fields
    if project_data.name is not None:
        project.name = project_data.name
    
    if project_data.git_url is not None:
        project.git_url = project_data.git_url
    
    if project_data.slack_channel is not None:
        project.slack_channel = project_data.slack_channel
    
    if project_data.max_parallel_tasks is not None:
        project.max_parallel_tasks = project_data.max_parallel_tasks
    
    if project_data.documents is not None:
        project.documents = project_data.documents
    
    if project_data.features is not None:
        project.features = project_data.features
    
    if project_data.implementation_plan is not None:
        project.implementation_plan = project_data.implementation_plan
    
    # Save the updated project
    if not project_database.save_project(project):
        raise HTTPException(status_code=500, detail="Failed to update project")
    
    return ProjectModel(
        id=project.id,
        name=project.name,
        git_url=project.git_url,
        slack_channel=project.slack_channel,
        max_parallel_tasks=project.max_parallel_tasks,
        documents=project.documents,
        features=project.features,
        implementation_plan=project.implementation_plan,
        created_at=datetime.fromisoformat(project.created_at),
        updated_at=datetime.fromisoformat(project.updated_at)
    )

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    project_database: ProjectDatabase = Depends(get_project_database)
):
    """Delete a project."""
    project = project_database.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project_database.delete_project(project_id):
        raise HTTPException(status_code=500, detail="Failed to delete project")
    
    return {"message": f"Project {project_id} deleted successfully"}

@router.post("/{project_id}/documents")
async def add_document(
    project_id: str,
    document: UploadFile = File(...),
    category: str = Form(...),
    project_database: ProjectDatabase = Depends(get_project_database)
):
    """Add a document to a project."""
    project = project_database.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create the document directory if it doesn't exist
    import os
    doc_dir = f"docs/{project_id}/{category}"
    os.makedirs(doc_dir, exist_ok=True)
    
    # Save the document
    file_path = f"{doc_dir}/{document.filename}"
    with open(file_path, "wb") as f:
        f.write(await document.read())
    
    # Add the document to the project
    if not project_database.add_document_to_project(project_id, file_path):
        raise HTTPException(status_code=500, detail="Failed to add document to project")
    
    return {"message": f"Document {document.filename} added to project {project_id}"}

@router.post("/{project_id}/analyze")
async def analyze_project(
    project_id: str,
    ai_user_agent = Depends(get_ai_user_agent)
):
    """Analyze project requirements and create an implementation plan."""
    # Analyze project requirements
    requirements = ai_user_agent.analyze_project_requirements(project_id)
    if not requirements:
        raise HTTPException(status_code=500, detail="Failed to analyze project requirements")
    
    # Create implementation plan
    implementation_plan = ai_user_agent.create_implementation_plan(project_id)
    if not implementation_plan:
        raise HTTPException(status_code=500, detail="Failed to create implementation plan")
    
    return {
        "message": "Project analyzed successfully",
        "requirements": requirements,
        "implementation_plan": implementation_plan
    }

@router.put("/{project_id}/tasks/{task_id}")
async def update_task_status(
    project_id: str,
    task_id: str,
    status: str,
    project_database: ProjectDatabase = Depends(get_project_database)
):
    """Update the status of a task."""
    project = project_database.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.implementation_plan:
        raise HTTPException(status_code=404, detail="Implementation plan not found")
    
    # Find the task
    tasks = project.implementation_plan.get('tasks', [])
    task = next((t for t in tasks if t.get('id') == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update the task status
    task['status'] = status
    if status == 'completed':
        task['completed_at'] = datetime.now().timestamp()
    
    # Save the updated project
    project.implementation_plan['tasks'] = tasks
    if not project_database.save_project(project):
        raise HTTPException(status_code=500, detail="Failed to update task status")
    
    return {"message": f"Task {task_id} status updated to {status}"}

@router.get("/{project_id}/recent-activity")
async def get_recent_activity(
    project_id: str,
    days: int = 7,
    project_database: ProjectDatabase = Depends(get_project_database),
    github_manager = Depends(get_github_manager)
):
    """Get recent activity for a project."""
    project = project_database.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get repository owner and name
    repo_url = project.git_url
    repo_parts = repo_url.rstrip('/').split('/')
    repo_name = repo_parts[-1].replace('.git', '')
    repo_owner = repo_parts[-2]
    
    # Get recent merges
    merges = github_manager.get_recent_merges(
        owner=repo_owner,
        repo=repo_name,
        days=days
    )
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "recent_merges": merges
    }