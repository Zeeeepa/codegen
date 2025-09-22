Orchestrator (MVP)
- api: FastAPI service for projects/repos/branches/PRs/runs/analyses, SSE streams
- workers: simple polling workers for Codegen logs and Graph-sitter findings
- web: minimal React/Vite UI for project cards (proxy to /api)

Run API
- see orchestrator/api/README.md

Run Web
- cd orchestrator/web && npm install && npm run dev
- proxy routes to API at http://127.0.0.1:8001

