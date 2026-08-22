from __future__ import annotations

import json
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


BASE = "http://127.0.0.1:8000"
ENDPOINTS = [
    "/health",
    "/metrics",
    "/elite/status",
    "/proof/live",
    "/root-cause",
    "/incidents",
    "/optimization/proof",
    "/architecture",
    "/metrics/prometheus",
]


def fetch(path: str) -> tuple[bool, str]:
    try:
        with urlopen(f"{BASE}{path}", timeout=5) as response:
            body = response.read(500).decode("utf-8", errors="replace")
            return response.status < 400, body
    except URLError as exc:
        return False, str(exc)
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    print("AstraOS final health check")
    print(f"Runtime: {BASE}")
    print(f"Timestamp: {time.ctime()}")
    print()

    results = []
    for endpoint in ENDPOINTS:
        ok, body = fetch(endpoint)
        results.append(ok)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {endpoint}")
        if not ok:
            print(f"       {body}")

    dashboard_ok, dashboard_body = fetch_dashboard()
    results.append(dashboard_ok)
    print(f"[{'PASS' if dashboard_ok else 'FAIL'}] dashboard http://127.0.0.1:5173")
    if not dashboard_ok:
        print(f"       {dashboard_body}")

    summary = {
        "passed": sum(1 for item in results if item),
        "total": len(results),
        "status": "ready" if all(results) else "needs_runtime_start",
    }
    print()
    print(json.dumps(summary, indent=2))
    return 0 if all(results) else 1


def fetch_dashboard() -> tuple[bool, str]:
    try:
        with urlopen("http://127.0.0.1:5173", timeout=5) as response:
            return response.status < 400, response.read(120).decode("utf-8", errors="replace")
    except Exception as exc:
        return False, str(exc)


if __name__ == "__main__":
    sys.exit(main())
