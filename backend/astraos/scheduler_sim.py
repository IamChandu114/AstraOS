from __future__ import annotations

import time
from typing import Any

from backend.astraos.process_filters import user_processes


class SchedulerSimulator:
    """Compare Linux CFS-style baseline with AstraOS policies using real process telemetry."""

    def compare(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        processes = user_processes(snapshot.get("processes", {}).get("top", []))[:24]
        cores = max(1, int(snapshot.get("cpu", {}).get("logical_cores") or 1))
        cfs = self._cfs(processes, cores)
        astra = self._astra(processes, cores)
        return {
            "timestamp": time.time(),
            "cores": cores,
            "process_count": len(processes),
            "linux_cfs": cfs,
            "astra_scheduler": astra,
            "improvement_estimate": {
                "core_balance_delta": round(cfs["imbalance"] - astra["imbalance"], 3),
                "latency_score_delta": round(astra["latency_score"] - cfs["latency_score"], 3),
            },
        }

    def _cfs(self, processes: list[dict[str, Any]], cores: int) -> dict[str, Any]:
        buckets = [0.0 for _ in range(cores)]
        timeline = []
        for index, proc in enumerate(processes):
            core = index % cores
            load = float(proc.get("cpu_percent") or 0)
            buckets[core] += load
            timeline.append({"pid": proc.get("pid"), "process": proc.get("name"), "core": core, "load": load})
        return self._summary(buckets, timeline)

    def _astra(self, processes: list[dict[str, Any]], cores: int) -> dict[str, Any]:
        buckets = [0.0 for _ in range(cores)]
        timeline = []
        for proc in sorted(processes, key=lambda item: float(item.get("cpu_percent") or 0), reverse=True):
            core = min(range(cores), key=lambda idx: buckets[idx])
            load = float(proc.get("cpu_percent") or 0)
            buckets[core] += load
            timeline.append({"pid": proc.get("pid"), "process": proc.get("name"), "core": core, "load": load})
        return self._summary(buckets, timeline)

    def _summary(self, buckets: list[float], timeline: list[dict[str, Any]]) -> dict[str, Any]:
        average = sum(buckets) / max(1, len(buckets))
        imbalance = sum(abs(value - average) for value in buckets) / max(1, len(buckets))
        latency_score = max(0.0, 100.0 - imbalance)
        return {
            "core_loads": [round(value, 2) for value in buckets],
            "imbalance": round(imbalance, 3),
            "latency_score": round(latency_score, 3),
            "timeline": timeline,
        }
