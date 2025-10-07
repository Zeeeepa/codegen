from __future__ import annotations

import os
import time
import requests

API_BASE = os.getenv("ORCH_API_BASE", "http://127.0.0.1:8001")
INTERVAL = int(os.getenv("ORCH_LOG_COLLECT_INTERVAL", "5"))


def main():
    while True:
        try:
            runs = requests.get(f"{API_BASE}/runs").json() if False else []  # list endpoint not implemented; scan recent ids
            # Simple heuristic: try last N run ids
            for run_id in range(1, 51):
                try:
                    requests.post(f"{API_BASE}/runs/{run_id}/poll", timeout=10)
                except Exception:
                    pass
        except Exception as e:
            print("log_collector error", e)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()

