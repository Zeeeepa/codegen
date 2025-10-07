from __future__ import annotations

import asyncio
import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from ..db import get_session
from .. import models, schemas
from ..adapters.codegen_adapter import CodegenAdapter

router = APIRouter()

CODEGEN_ORG_ID = os.getenv("CODEGEN_ORG_ID")


@router.post("/", response_model=schemas.AgentRunOut)
def register_run(payload: schemas.AgentRunCreate, session: Session = Depends(get_session)):
    repo = session.get(models.Repository, payload.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    run = models.AgentRun(
        provider=payload.provider,
        external_id=payload.external_id,
        repository_id=repo.id,
        branch_id=payload.branch_id,
        status="registered",
        web_url=None,
    )
    session.add(run)
    session.flush()
    return run


@router.post("/{run_id}/poll", response_model=dict)
def poll_run_logs(run_id: int, skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    run = session.get(models.AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.provider != "codegen":
        raise HTTPException(status_code=400, detail="Only codegen runs supported")
    org = CODEGEN_ORG_ID
    if not org:
        raise HTTPException(status_code=400, detail="CODEGEN_ORG_ID env not set")
    adapter = CodegenAdapter(org)
    data = adapter.get_run_logs(run.external_id, skip=skip, limit=limit)
    total = 0
    for log in data.get("logs", []):
        evt = models.AgentRunEvent(
            agent_run_id=run.id,
            type=log.get("message_type", "ACTION"),
            tool_name=log.get("tool_name"),
            thought=log.get("thought"),
            observation=str(log.get("observation")),
            tool_input=str(log.get("tool_input")),
            tool_output=str(log.get("tool_output")),
        )
        session.add(evt)
        total += 1
    session.flush()
    return {"stored": total, "status": data.get("status"), "total_logs": data.get("total_logs")}


@router.get("/{run_id}/events/stream")
async def stream_run_events(run_id: int, session: Session = Depends(get_session)):
    run = session.get(models.AgentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    async def gen():
        last_id = 0
        while True:
            # Poll DB for new events
            events = (
                session.query(models.AgentRunEvent)
                .filter(models.AgentRunEvent.agent_run_id == run.id, models.AgentRunEvent.id > last_id)
                .order_by(models.AgentRunEvent.id.asc())
                .all()
            )
            for e in events:
                last_id = e.id
                yield {
                    "event": e.type.lower(),
                    "id": str(e.id),
                    "data": {
                        "tool": e.tool_name,
                        "thought": e.thought,
                        "observation": e.observation,
                        "tool_input": e.tool_input,
                        "tool_output": e.tool_output,
                    },
                }
            await asyncio.sleep(1.0)

    return EventSourceResponse(gen())

