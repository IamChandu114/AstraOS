from __future__ import annotations

import time
from typing import Any


class ResearchReportGenerator:
    """Generate research-style reports from actual AstraOS runtime outputs."""

    def generate(
        self,
        latest: dict[str, Any] | None,
        prediction: dict[str, Any] | None,
        benchmark: dict[str, Any] | None,
        scheduler: dict[str, Any] | None,
        healing: dict[str, Any] | None,
    ) -> dict[str, Any]:
        sections = [
            self._section("System State", latest),
            self._section("AI Forecast", prediction),
            self._section("Benchmark Evidence", benchmark),
            self._section("Scheduler Comparison", scheduler),
            self._section("Self-Healing Analysis", healing),
        ]
        markdown = "# AstraOS Runtime Research Report\n\n"
        markdown += f"Generated at `{time.ctime()}` from live telemetry.\n\n"
        for section in sections:
            markdown += f"## {section['title']}\n\n{section['body']}\n\n"
        return {"timestamp": time.time(), "format": "markdown", "report": markdown, "sections": sections}

    def _section(self, title: str, payload: dict[str, Any] | None) -> dict[str, str]:
        if not payload:
            return {"title": title, "body": "No live data available for this section."}
        if title == "System State":
            body = (
                f"- CPU usage: {payload.get('cpu', {}).get('usage_percent')}%\n"
                f"- Memory usage: {payload.get('memory', {}).get('percent')}%\n"
                f"- Process count: {payload.get('processes', {}).get('total')}\n"
                f"- Thermal hottest sensor: {payload.get('thermal', {}).get('hottest_c')}\n"
            )
        elif title == "AI Forecast":
            body = (
                f"- Workload class: {payload.get('workload_class')}\n"
                f"- CPU risk: {payload.get('cpu_spike', {}).get('risk')}\n"
                f"- Memory risk: {payload.get('memory_pressure', {}).get('risk')}\n"
                f"- Recommendations: {', '.join(payload.get('recommendations', []))}\n"
            )
        elif title == "Benchmark Evidence":
            body = "\n".join(
                f"- {item.get('name')}: {item.get('before')} -> {item.get('after')} {item.get('unit')}"
                for item in payload.get("metrics", [])
            ) or "No benchmark metrics recorded."
        elif title == "Scheduler Comparison":
            improvement = payload.get("improvement_estimate", {})
            body = (
                f"- Core balance delta: {improvement.get('core_balance_delta')}\n"
                f"- Latency score delta: {improvement.get('latency_score_delta')}\n"
            )
        else:
            body = "\n".join(
                f"- {item.get('type')}: {item.get('severity')}"
                for item in payload.get("incidents", [])
            ) or "No incidents detected."
        return {"title": title, "body": body}
