from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_session
from .. import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.ProjectOut)
def create_project(payload: schemas.ProjectCreate, session: Session = Depends(get_session)):
    existing = session.query(models.Project).filter(models.Project.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project name already exists")
    project = models.Project(name=payload.name, description=payload.description)
    session.add(project)
    session.flush()
    return project


@router.get("/", response_model=list[schemas.ProjectOut])
def list_projects(session: Session = Depends(get_session)):
    items = session.query(models.Project).order_by(models.Project.created_at.desc()).all()
    return items


@router.post("/{project_id}/link", response_model=dict)
def link_repository(project_id: int, link: schemas.ProjectRepositoryLink, session: Session = Depends(get_session)):
    project = session.get(models.Project, project_id)
    repo = session.get(models.Repository, link.repository_id)
    if not project or not repo:
        raise HTTPException(status_code=404, detail="Project or repository not found")
    existing = (
        session.query(models.ProjectRepository)
        .filter(models.ProjectRepository.project_id == project_id, models.ProjectRepository.repository_id == link.repository_id)
        .first()
    )
    if existing:
        return {"status": "already_linked"}
    pr = models.ProjectRepository(project_id=project_id, repository_id=link.repository_id)
    session.add(pr)
    return {"status": "linked"}

