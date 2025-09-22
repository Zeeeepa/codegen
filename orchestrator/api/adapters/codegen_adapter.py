from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

CODEGEN_API_URL = os.getenv("CODEGEN_API_URL", "https://api.codegen.com")
CODEGEN_API_TOKEN = os.getenv("CODEGEN_API_TOKEN")


class CodegenAdapter:
    def __init__(self, org_id: str):
        self.org_id = org_id
        if not CODEGEN_API_TOKEN:
            raise RuntimeError("CODEGEN_API_TOKEN is not set")
        self._client = httpx.Client(base_url=CODEGEN_API_URL, headers={
            "Authorization": f"Bearer {CODEGEN_API_TOKEN}",
            "Content-Type": "application/json",
        }, timeout=30.0)

    def get_run_logs(self, agent_run_id: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        url = f"/v1/organizations/{self.org_id}/agent/run/{agent_run_id}/logs"
        params = {"skip": skip, "limit": limit}
        resp = self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    # Placeholder for potential run start / PR creation via Codegen
    # def create_pr(...): pass

