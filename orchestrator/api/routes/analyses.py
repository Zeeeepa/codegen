from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from ..db import get_session
from .. import models, schemas
from ..adapters.analysis_adapter import AnalysisAdapter

router = APIRouter()


@router.post("/", response_model=schemas.AnalysisOut)
def start_analysis(payload: schemas.AnalysisStart, session: Session = Depends(get_session)):
    repo = session.get(models.Repository, payload.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    branch = session.get(models.Branch, payload.branch_id) if payload.branch_id else None
    branch_name = branch.name if branch else repo.default_branch

    # Call analysis server
    try:
        adapter = AnalysisAdapter()
        res = adapter.start_analysis(f"{repo.org}/{repo.name}", branch_name, None)
        external_id = str(res.get("id") or res.get("analysis_id") or "")
    except Exception as e:
        external_id = ""

    analysis = models.Analysis(
        repository_id=repo.id,
        branch_id=payload.branch_id,
        snapshot_id=payload.snapshot_id,
        status="running",
        started_at=datetime.utcnow(),
        external_id=external_id or None,
    )
    session.add(analysis)
    session.flush()
    return analysis


@router.post("/{analysis_id}/poll", response_model=dict)
def poll_findings(analysis_id: int, skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    analysis = session.get(models.Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if not analysis.external_id:
        return {"stored": 0, "status": analysis.status}

    adapter = AnalysisAdapter()
    try:
        data = adapter.get_findings(analysis.external_id, skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis fetch failed: {e}")

    stored = 0
    for f in data.get("findings", []):
        finding = models.Finding(
            analysis_id=analysis.id,
            type=str(f.get("type") or "unknown"),
            file=f.get("file"),
            start_line=f.get("start_line"),
            end_line=f.get("end_line"),
            symbol=f.get("symbol"),
            context=str(f.get("context") or ""),
            confidence=f.get("confidence"),
            status="open",
        )
        session.add(finding)
        stored += 1
    session.flush()

    return {"stored": stored, "status": analysis.status}


@router.get("/{analysis_id}/stream")
async def stream_findings(analysis_id: int, session: Session = Depends(get_session)):
    analysis = session.get(models.Analysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    async def gen():
        last_id = 0
        while True:
            records = (
                session.query(models.Finding)
                .filter(models.Finding.analysis_id == analysis.id, models.Finding.id > last_id)
                .order_by(models.Finding.id.asc())
                .all()
            )
            for f in records:
                last_id = f.id
                yield {
                    "event": f.type,
                    "id": str(f.id),
                    "data": {
                        "file": f.file,
                        "range": [f.start_line, f.end_line],
                        "symbol": f.symbol,
                        "context": f.context,
                        "confidence": f.confidence,
                        "status": f.status,
                    },
                }
            await asyncio.sleep(1.0)

    return EventSourceResponse(gen())

