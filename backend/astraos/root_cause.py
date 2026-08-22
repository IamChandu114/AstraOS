from __future__ import annotations

import time
from typing import Any

from backend.astraos.process_filters import is_protected_process


class RootCauseAnalyzer:
    """Explain resource pressure using live telemetry and AI forecast context."""

    def analyze(self, snapshot: dict[str, Any] | None, prediction: dict[str, Any] | None = None) -> dict[str, Any]:
        if not snapshot:
            return {
                "timestamp": time.time(),
                "status": "warming_up",
                "summary": "Root-cause analysis is waiting for live telemetry samples.",
                "findings": [],
            }

        findings = []
        processes = snapshot.get("processes", {}).get("top", [])
        cpu = float(snapshot.get("cpu", {}).get("usage_percent") or 0)
        memory = float(snapshot.get("memory", {}).get("percent") or 0)
        swap = float(snapshot.get("swap", {}).get("percent") or 0)
        temp = snapshot.get("thermal", {}).get("hottest_c")
        network_rx = float(snapshot.get("network", {}).get("bytes_recv_per_sec") or 0)
        network_tx = float(snapshot.get("network", {}).get("bytes_sent_per_sec") or 0)

        cpu_offenders = self._rank(processes, "cpu_percent", 5)
        mem_offenders = self._rank(processes, "memory_percent", 5)

        if cpu > 70 or prediction_risk(prediction, "cpu_spike"):
            findings.append(self._finding(
                "cpu_pressure",
                "CPU pressure is correlated with high per-process CPU usage.",
                cpu_offenders,
                min(0.98, 0.55 + cpu / 180),
                "Apply guarded priority balancing or CPU affinity to non-critical offenders.",
            ))

        if memory > 75 or swap > 15 or prediction_risk(prediction, "memory_pressure"):
            memory_forecast = (prediction or {}).get("memory_pressure", {})
            memory_reasoning = [
                "Memory pressure is correlated with resident process growth and cache pressure.",
                f"Current memory is {memory_forecast.get('current', memory)}%; 60-second forecast is {memory_forecast.get('forecast_60s', 'unknown')}%.",
            ]
            if memory_forecast.get("expected_failure_label"):
                memory_reasoning.append(f"Projected exhaustion window: {memory_forecast['expected_failure_label']}.")
            memory_reasoning.extend(memory_forecast.get("reasoning") or [])
            findings.append(self._finding(
                "memory_pressure",
                memory_reasoning,
                mem_offenders,
                min(0.97, 0.5 + memory / 190 + swap / 300),
                "Inspect high-memory processes, reclaim cache only with operator approval, and isolate leak candidates.",
            ))

        if temp is not None and (float(temp) > 78 or prediction_risk(prediction, "thermal")):
            findings.append({
                "type": "thermal_pressure",
                "severity": "critical" if float(temp) > 88 else "warning",
                "confidence": min(0.96, 0.52 + float(temp) / 180),
                "reasoning": [
                    f"Hottest reported sensor is {temp} C.",
                    "Thermal pressure generally follows sustained CPU/GPU utilization.",
                    "AstraOS will prefer workload migration or throttling recommendations before unsafe power changes.",
                ],
                "contributors": cpu_offenders[:3],
                "recommended_action": "Migrate or reduce sustained CPU/GPU workloads until thermal headroom recovers.",
            })

        if (network_rx + network_tx) > 20 * 1024 * 1024:
            findings.append({
                "type": "network_pressure",
                "severity": "warning",
                "confidence": 0.86,
                "reasoning": [
                    f"Network throughput is {round((network_rx + network_tx) / 1024 / 1024, 2)} MiB/s.",
                    "High network activity can destabilize distributed inference or telemetry delivery.",
                ],
                "contributors": [],
                "recommended_action": "Prefer bandwidth-aware node selection and reduce non-critical synchronization traffic.",
            })

        if not findings:
            findings.append({
                "type": "stable_runtime",
                "severity": "info",
                "confidence": 0.82,
                "reasoning": ["No dominant CPU, memory, thermal, or network pressure is visible in the latest live sample."],
                "contributors": [],
                "recommended_action": "Continue observing; no optimization is currently required.",
            })

        return {
            "timestamp": time.time(),
            "status": "live",
            "workload_class": prediction.get("workload_class") if prediction else "classifier warming",
            "summary": self._summary(findings),
            "findings": findings,
        }

    def _rank(self, processes: list[dict[str, Any]], key: str, limit: int) -> list[dict[str, Any]]:
        ranked = sorted(processes, key=lambda proc: float(proc.get(key) or 0), reverse=True)
        return [
            {
                "pid": proc.get("pid"),
                "name": proc.get("name"),
                "cpu_percent": proc.get("cpu_percent"),
                "memory_percent": proc.get("memory_percent"),
                "threads": proc.get("threads"),
                "protected": is_protected_process(proc),
            }
            for proc in ranked[:limit]
            if float(proc.get(key) or 0) > 0
        ]

    def _finding(
        self,
        kind: str,
        message: str,
        contributors: list[dict[str, Any]],
        confidence: float,
        action: str,
    ) -> dict[str, Any]:
        severity = "critical" if confidence > 0.9 else "warning" if confidence > 0.74 else "info"
        names = [str(item.get("name")) for item in contributors[:3] if item.get("name")]
        reasoning = message if isinstance(message, list) else [message]
        if names:
            reasoning.append(f"Top correlated processes: {', '.join(names)}.")
        reasoning.append("Protected system processes are excluded from automatic execution policies.")
        return {
            "type": kind,
            "severity": severity,
            "confidence": round(confidence, 3),
            "reasoning": reasoning,
            "contributors": contributors,
            "recommended_action": action,
        }

    def _summary(self, findings: list[dict[str, Any]]) -> str:
        primary = findings[0]
        if primary["type"] == "stable_runtime":
            return "Runtime is stable; AstraOS is staying in observe mode."
        return f"{primary['type'].replace('_', ' ').title()} detected with {round(primary['confidence'] * 100, 1)}% confidence."


def prediction_risk(prediction: dict[str, Any] | None, key: str) -> bool:
    if not prediction:
        return False
    return prediction.get(key, {}).get("risk") in {"warning", "critical"}
