from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_session
from .. import models, schemas
from ..adapters.github_adapter import GitHubAdapter

router = APIRouter()


@router.post("/", response_model=schemas.PROut)
def open_pr(payload: schemas.PROpenRequest, session: Session = Depends(get_session)):
    repo = session.get(models.Repository, payload.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Create PR on GitHub
    try:
        gh = GitHubAdapter()
        pr_json = gh.create_pr(repo.org, repo.name, payload.head_branch, payload.base_branch, payload.title, payload.body)
        pr_number = pr_json["number"]
        web_url = pr_json.get("html_url")
        # map head_branch -> branch id
        br = (
            session.query(models.Branch)
            .filter(models.Branch.repository_id == repo.id, models.Branch.name == payload.head_branch)
            .first()
        )
        if not br:
            br = models.Branch(repository_id=repo.id, name=payload.head_branch)
            session.add(br)
            session.flush()
        pr = models.PullRequest(
            repository_id=repo.id,
            number=pr_number,
            head_branch_id=br.id,
            base_branch=payload.base_branch,
            state=pr_json.get("state", "open"),
            checks_status=None,
            web_url=web_url,
        )
        session.add(pr)
        session.flush()
        return pr
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open PR: {e}")

