Project Orchestrator API (MVP)

Quick start
1) Python 3.12+ recommended
2) Install deps:
   pip install -r orchestrator/api/requirements.txt
3) Set env:
   export ORCH_DATABASE_URL=sqlite:///./orchestrator.db
   export CODEGEN_API_URL=https://api.codegen.com
   export CODEGEN_API_TOKEN=[REDACTED]
   export CODEGEN_ORG_ID=[YOUR_ORG_ID]
   export GITHUB_TOKEN=[REDACTED]
   export GRAPH_SITTER_URL=http://localhost:8080
4) Run server:
   uvicorn orchestrator.api.app:app --reload --port 8001

Endpoints (selection)
- GET /health
- POST /projects, GET /projects
- POST /repos, GET /repos, POST /repos/pin, POST /repos/unpin
- GET /branches?repository_id=1, POST /branches
- POST /prs
- POST /runs, POST /runs/{id}/poll, GET /runs/{id}/events/stream (SSE)
- POST /analyses, POST /analyses/{id}/poll, GET /analyses/{id}/stream (SSE)

Notes
- SQLite used for MVP; swap ORCH_DATABASE_URL to Postgres in production.
- SSE endpoints poll DB periodically; wire a worker to call /runs/{id}/poll and /analyses/{id}/poll on intervals.
- Graph-sitter API contract assumed; adapt adapter if your server exposes different routes.

