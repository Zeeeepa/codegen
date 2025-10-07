from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_session
from .. import models, schemas
from ..adapters.github_adapter import GitHubAdapter

router = APIRouter()


@router.get("/", response_model=list[schemas.BranchOut])
def list_branches(repository_id: int, session: Session = Depends(get_session)):
    items = session.query(models.Branch).filter(models.Branch.repository_id == repository_id).all()
    return items


@router.post("/", response_model=schemas.BranchOut)
def create_branch(payload: schemas.BranchCreate, session: Session = Depends(get_session)):
    repo = session.get(models.Repository, payload.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Try to create branch in GitHub
    try:
        gh = GitHubAdapter()
        gh.create_branch(repo.org, repo.name, payload.name, payload.from_ref or repo.default_branch)
        # Fetch head SHA for the new branch
        ref = gh.get_branch(repo.org, repo.name, payload.name)
        head_sha = ref["object"]["sha"]
    except Exception as e:
        # Still create a local branch record for tracking, but without head_sha
        head_sha = None

    # Persist branch
    existing = (
        session.query(models.Branch)
        .filter(models.Branch.repository_id == repo.id, models.Branch.name == payload.name)
        .first()
    )
    if existing:
        if head_sha:
            existing.head_sha = head_sha
        return existing

    br = models.Branch(repository_id=repo.id, name=payload.name, head_sha=head_sha, status=None)
    session.add(br)
    session.flush()
    return br

