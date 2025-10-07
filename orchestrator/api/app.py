from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.background import BackgroundTasks
from sse_starlette.sse import EventSourceResponse

from .db import Base, engine, get_session
from .routes import projects, repos, branches, prs, runs, analyses

app = FastAPI(title="Project Orchestrator API", version="0.1.0")

# CORS for local dev; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


# Routers
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(repos.router, prefix="/repos", tags=["repos"])
app.include_router(branches.router, prefix="/branches", tags=["branches"])
app.include_router(prs.router, prefix="/prs", tags=["prs"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(analyses.router, prefix="/analyses", tags=["analyses"])


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})

