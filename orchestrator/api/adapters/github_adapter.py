from __future__ import annotations

import os
from typing import Optional, Dict, Any

import httpx

GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


class GitHubAdapter:
    def __init__(self):
        if not GITHUB_TOKEN:
            raise RuntimeError("GITHUB_TOKEN is not set")
        self._client = httpx.Client(base_url=GITHUB_API_URL, headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
        }, timeout=30.0)

    def get_repo(self, org: str, name: str) -> Dict[str, Any]:
        r = self._client.get(f"/repos/{org}/{name}")
        r.raise_for_status()
        return r.json()

    def get_branch(self, org: str, name: str, branch: str) -> Dict[str, Any]:
        r = self._client.get(f"/repos/{org}/{name}/git/ref/heads/{branch}")
        r.raise_for_status()
        return r.json()

    def create_branch(self, org: str, name: str, branch: str, from_ref: Optional[str] = None) -> Dict[str, Any]:
        # Determine base SHA
        base_branch = from_ref or self.get_repo(org, name).get("default_branch", "main")
        ref_data = self.get_branch(org, name, base_branch)
        base_sha = ref_data["object"]["sha"]
        # Create new ref
        payload = {"ref": f"refs/heads/{branch}", "sha": base_sha}
        r = self._client.post(f"/repos/{org}/{name}/git/refs", json=payload)
        r.raise_for_status()
        return r.json()

    def create_pr(self, org: str, name: str, head_branch: str, base_branch: str, title: str, body: Optional[str] = None) -> Dict[str, Any]:
        payload = {"title": title, "head": head_branch, "base": base_branch, "body": body or ""}
        r = self._client.post(f"/repos/{org}/{name}/pulls", json=payload)
        r.raise_for_status()
        return r.json()

    def get_pr_checks(self, org: str, name: str, pr_number: int) -> Dict[str, Any]:
        # Use the Checks API indirectly via PR HEAD SHA
        pr = self._client.get(f"/repos/{org}/{name}/pulls/{pr_number}")
        pr.raise_for_status()
        head_sha = pr.json()["head"]["sha"]
        checks = self._client.get(f"/repos/{org}/{name}/commits/{head_sha}/check-runs")
        checks.raise_for_status()
        return checks.json()

