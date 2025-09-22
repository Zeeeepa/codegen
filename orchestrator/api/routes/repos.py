from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_session
from .. import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.RepositoryOut)
def create_repo(payload: schemas.RepositoryCreate, session: Session = Depends(get_session)):
    existing = (
        session.query(models.Repository)
        .filter(models.Repository.provider == payload.provider,
                models.Repository.org == payload.org,
                models.Repository.name == payload.name)
        .first()
    )
    if existing:
        return existing
    repo = models.Repository(
        provider=payload.provider,
        org=payload.org,
        name=payload.name,
        default_branch=payload.default_branch,
        visibility=payload.visibility,
    )
    session.add(repo)
    session.flush()
    return repo


@router.get("/", response_model=list[schemas.RepositoryOut])
def list_repos(session: Session = Depends(get_session)):
    items = session.query(models.Repository).all()
    return items


@router.post("/pin", response_model=dict)
def pin_repo(pin: schemas.PinCreate, session: Session = Depends(get_session)):
    existing = (
        session.query(models.Pin)
        .filter(
            models.Pin.project_id == pin.project_id,
            models.Pin.repository_id == pin.repository_id,
            models.Pin.user_id == pin.user_id,
        )
        .first()
    )
    if existing:
        return {"status": "already_pinned"}
    p = models.Pin(project_id=pin.project_id, repository_id=pin.repository_id, user_id=pin.user_id)
    session.add(p)
    return {"status": "pinned"}


@router.post("/unpin", response_model=dict)
def unpin_repo(pin: schemas.PinCreate, session: Session = Depends(get_session)):
    existing = (
        session.query(models.Pin)
        .filter(
            models.Pin.project_id == pin.project_id,
            models.Pin.repository_id == pin.repository_id,
            models.Pin.user_id == pin.user_id,
        )
        .first()
    )
    if not existing:
        return {"status": "not_pinned"}
    session.delete(existing)
    return {"status": "unpinned"}

