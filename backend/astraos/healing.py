from __future__ import annotations

import time
from typing import Any

from backend.astraos.process_filters import is_protected_process


class SelfHealingEngine:
    """Detect instability from real telemetry and produce recovery plans."""

    def evaluate(self, history: list[dict[str, Any]], prediction: dict[str, Any] | None = None) -> dict[str, Any]:
        if not history:
            return {"timestamp": time.time(), "status": "warming_up", "incidents": [], "recovery_plan": []}
        latest = history[-1]
        incidents = []
        top = latest.get("processes", {}).get("top", [])

        for proc in top[:12]:
            if is_protected_process(proc):
                continue
            cpu = float(proc.get("cpu_percent") or 0)
            memory = float(proc.get("memory_percent") or 0)
            if cpu > 85:
                incidents.append({"type": "runaway_cpu", "pid": proc.get("pid"), "process": proc.get("name"), "severity": "high", "value": cpu})
            if memory > 12:
                incidents.append({"type": "memory_leak_candidate", "pid": proc.get("pid"), "process": proc.get("name"), "severity": "medium", "value": memory})

        if prediction and prediction.get("anomaly", {}).get("is_anomaly"):
            incidents.append({"type": "resource_anomaly", "severity": "high", "value": prediction.get("anomaly", {}).get("score")})
        if float(latest.get("memory", {}).get("percent") or 0) > 90:
            incidents.append({"type": "system_memory_pressure", "severity": "high", "value": latest.get("memory", {}).get("percent")})

        plan = [self._mitigation(incident) for incident in incidents]
        return {
            "timestamp": time.time(),
            "status": "live",
            "incidents": incidents,
            "recovery_plan": plan,
            "timeline": [{"timestamp": latest.get("timestamp"), "event": item["type"], "severity": item["severity"]} for item in incidents],
        }

    def _mitigation(self, incident: dict[str, Any]) -> dict[str, Any]:
        mapping = {
            "runaway_cpu": "throttle_or_renice_process",
            "memory_leak_candidate": "isolate_and_watch_memory_growth",
            "resource_anomaly": "increase_sampling_and_generate_incident_report",
            "system_memory_pressure": "trim_cache_and_protect_foreground_working_sets",
        }
        return {
            "incident": incident,
            "action": mapping.get(incident["type"], "observe"),
            "apply_mode": "requires_ASTRAOS_ENABLE_APPLY",
        }
