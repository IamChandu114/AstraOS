from __future__ import annotations

import time
from typing import Any


class ProofPackager:
    def build(
        self,
        snapshot: dict[str, Any] | None,
        history: list[dict[str, Any]],
        prediction: dict[str, Any] | None,
        optimization_plan: dict[str, Any] | None,
        distributed: dict[str, Any],
        capabilities: list[dict[str, Any]],
        benchmarks: dict[str, Any] | None,
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "timestamp": time.time(),
            "purpose": "Proof that AstraOS is connected to real host collectors and explicit simulation adapters.",
            "source_collectors": [
                "psutil",
                "procfs/sysfs when running on Linux",
                "nvidia-smi when present",
                "Docker CLI when present",
                "kubectl when configured",
                "perf/bpftrace when running on Linux with tooling",
            ],
            "raw_latest_telemetry": snapshot,
            "raw_history_tail": history[-10:],
            "raw_prediction": prediction,
            "raw_optimization_plan": optimization_plan,
            "distributed_fabric": distributed,
            "capability_matrix": capabilities,
            "benchmark_report": benchmarks,
            "operational_events": events,
            "process_evidence": (snapshot or {}).get("processes", {}).get("top", [])[:12],
        }
