from __future__ import annotations

import time
import uuid
from typing import Any


class IncidentTimelineEngine:
    """Create operational incident timelines from telemetry, AI forecasts, and execution logs."""

    def build(
        self,
        history: list[dict[str, Any]],
        prediction: dict[str, Any] | None,
        events: list[dict[str, Any]],
        root_cause: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = time.time()
        incident_type, severity = self._classify(history[-1] if history else None, prediction, root_cause)
        incident_id = f"inc-{uuid.uuid5(uuid.NAMESPACE_DNS, f'{incident_type}-{int(now // 60)}').hex[:10]}"
        timeline = []

        relevant = [
            event for event in events[-60:]
            if event.get("category") in {"telemetry", "ai", "risk", "predictive", "notification", "optimization", "stress", "chaos", "collector"}
        ]
        for event in relevant[-12:]:
            timeline.append({
                "timestamp": event.get("timestamp", now),
                "time": event.get("time") or time.strftime("%H:%M:%S", time.localtime(event.get("timestamp", now))),
                "phase": self._phase(event.get("category")),
                "severity": event.get("level", "info"),
                "message": event.get("message"),
                "node": event.get("node"),
                "confidence": event.get("confidence"),
            })

        if prediction:
            for key in ("cpu_spike", "memory_pressure", "thermal"):
                forecast = prediction.get(key, {})
                if forecast.get("risk") in {"warning", "critical"}:
                    timeline.append({
                        "timestamp": now,
                        "time": time.strftime("%H:%M:%S", time.localtime(now)),
                        "phase": "prediction",
                        "severity": forecast.get("risk"),
                        "message": f"AI predicts {key.replace('_', ' ')} risk with {round(float(forecast.get('confidence') or 0) * 100, 1)}% confidence.",
                        "node": "astra-ai-engine",
                        "confidence": forecast.get("confidence"),
                    })

        if root_cause and root_cause.get("findings"):
            primary = root_cause["findings"][0]
            timeline.append({
                "timestamp": now + 0.1,
                "time": time.strftime("%H:%M:%S", time.localtime(now)),
                "phase": "analysis",
                "severity": primary.get("severity", "info"),
                "message": root_cause.get("summary"),
                "node": "astra-rca-engine",
                "confidence": primary.get("confidence"),
            })

        timeline = sorted(timeline, key=lambda item: item.get("timestamp", 0))[-18:]
        first_ts = timeline[0]["timestamp"] if timeline else now
        last_ts = timeline[-1]["timestamp"] if timeline else now

        return {
            "incident_id": incident_id,
            "timestamp": now,
            "status": "active" if severity in {"warning", "critical"} else "stable",
            "type": incident_type,
            "severity": severity,
            "recovery_duration_seconds": round(max(0.0, last_ts - first_ts), 2),
            "timeline": timeline or [{
                "timestamp": now,
                "time": time.strftime("%H:%M:%S", time.localtime(now)),
                "phase": "observe",
                "severity": "info",
                "message": "No active incident. AstraOS is monitoring live telemetry.",
                "node": "astra-control-plane",
                "confidence": 0.82,
            }],
        }

    def _classify(
        self,
        snapshot: dict[str, Any] | None,
        prediction: dict[str, Any] | None,
        root_cause: dict[str, Any] | None,
    ) -> tuple[str, str]:
        if root_cause and root_cause.get("findings"):
            primary = root_cause["findings"][0]
            return primary.get("type", "runtime_observation"), primary.get("severity", "info")
        if not snapshot:
            return "collector_warmup", "info"
        cpu = float(snapshot.get("cpu", {}).get("usage_percent") or 0)
        memory = float(snapshot.get("memory", {}).get("percent") or 0)
        if prediction:
            for key in ("thermal", "memory_pressure", "cpu_spike"):
                risk = prediction.get(key, {}).get("risk")
                if risk == "critical":
                    return key, "critical"
                if risk == "warning":
                    return key, "warning"
        if cpu > 85:
            return "cpu_pressure", "critical"
        if memory > 85:
            return "memory_pressure", "critical"
        return "stable_runtime", "info"

    def _phase(self, category: str | None) -> str:
        return {
            "telemetry": "detection",
            "collector": "detection",
            "ai": "prediction",
            "risk": "risk",
            "predictive": "prediction",
            "notification": "notification",
            "optimization": "execution",
            "stress": "chaos",
            "chaos": "chaos",
        }.get(category or "", "observe")
