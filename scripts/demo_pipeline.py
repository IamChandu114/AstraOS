#!/usr/bin/env python3
"""Production smoke check for the live AstraOS runtime."""

from __future__ import annotations

import json
import urllib.request


API = "http://127.0.0.1:8000"


def fetch(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=5) as response:
        return json.loads(response.read().decode())


def main() -> None:
    health = fetch("/health")
    metrics = fetch("/metrics?limit=5")
    prediction = fetch("/predict")
    optimize = fetch("/optimize")
    nodes = fetch("/nodes")
    benchmarks = fetch("/benchmarks")
    elite = fetch("/elite/status")
    security = fetch("/security")
    twin = fetch("/digital-twin")
    scheduler = fetch("/scheduler/simulate")

    summary = {
        "health": health,
        "live_cpu_percent": metrics.get("latest", {}).get("cpu", {}).get("usage_percent"),
        "live_memory_percent": metrics.get("latest", {}).get("memory", {}).get("percent"),
        "live_processes": metrics.get("latest", {}).get("processes", {}).get("total"),
        "prediction": prediction,
        "optimization_plan": optimize,
        "nodes": nodes,
        "benchmarks": benchmarks,
        "elite_runtime": elite,
        "security": security,
        "digital_twin": twin,
        "scheduler_simulation": scheduler,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
