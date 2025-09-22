from __future__ import annotations

import os
from typing import Dict, Any, Optional

import httpx

GRAPH_SITTER_URL = os.getenv("GRAPH_SITTER_URL")  # e.g., http://graph-sitter:8000


class AnalysisAdapter:
    def __init__(self):
        if not GRAPH_SITTER_URL:
            raise RuntimeError("GRAPH_SITTER_URL is not set")
        self._client = httpx.Client(base_url=GRAPH_SITTER_URL, timeout=60.0)

    def start_analysis(self, repo_full_name: str, branch: str, snapshot_digest: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "repo": repo_full_name,
            "branch": branch,
            "snapshot": snapshot_digest,
        }
        r = self._client.post("/analyze", json=payload)
        r.raise_for_status()
        return r.json()

    def get_findings(self, analysis_id: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        r = self._client.get(f"/analyses/{analysis_id}/findings", params={"skip": skip, "limit": limit})
        r.raise_for_status()
        return r.json()

