from __future__ import annotations

import os
import time
import requests

API_BASE = os.getenv("ORCH_API_BASE", "http://127.0.0.1:8001")
INTERVAL = int(os.getenv("ORCH_ANALYSIS_POLL_INTERVAL", "10"))


def main():
    while True:
        try:
            # naive polling for analyses ids
            for analysis_id in range(1, 51):
                try:
                    requests.post(f"{API_BASE}/analyses/{analysis_id}/poll", timeout=10)
                except Exception:
                    pass
        except Exception as e:
            print("analysis_worker error", e)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()

