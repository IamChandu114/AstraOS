from __future__ import annotations

import time
from typing import Any


class OptimizationProofEngine:
    """Convert before/after runtime snapshots into measurable optimization evidence."""

    def summarize(self, optimization_result: dict[str, Any] | None, benchmark: dict[str, Any] | None = None) -> dict[str, Any]:
        if not optimization_result or not optimization_result.get("before") or not optimization_result.get("after"):
            return {
                "timestamp": time.time(),
                "status": "waiting_for_apply_run",
                "summary": "Run POST /optimize?apply=true with ASTRAOS_ENABLE_APPLY=1 to capture before/after execution proof.",
                "metrics": benchmark.get("metrics", []) if benchmark else [],
                "statements": self._benchmark_statements(benchmark),
            }

        before = optimization_result["before"]
        after = optimization_result["after"]
        metrics = [
            self._metric("CPU load", before.get("cpu", {}).get("usage_percent"), after.get("cpu", {}).get("usage_percent"), "%", lower_is_better=True),
            self._metric("Memory pressure", before.get("memory", {}).get("percent"), after.get("memory", {}).get("percent"), "%", lower_is_better=True),
            self._metric("Swap usage", before.get("swap", {}).get("percent"), after.get("swap", {}).get("percent"), "%", lower_is_better=True),
            self._metric("Process count", before.get("processes", {}).get("total"), after.get("processes", {}).get("total"), "processes", lower_is_better=True),
            self._metric("Thermal peak", before.get("thermal", {}).get("hottest_c"), after.get("thermal", {}).get("hottest_c"), "C", lower_is_better=True),
            self._metric(
                "Network throughput",
                self._network_total(before),
                self._network_total(after),
                "B/s",
                lower_is_better=False,
            ),
        ]
        metrics = [metric for metric in metrics if metric["before"] is not None and metric["after"] is not None]
        score = round(sum(metric["score"] for metric in metrics) / max(1, len(metrics)), 2)
        statements = self._statements(metrics)
        return {
            "timestamp": time.time(),
            "status": "measured",
            "execution_id": optimization_result.get("execution_id"),
            "execution_duration_ms": optimization_result.get("execution_duration_ms"),
            "rollback_available": bool(optimization_result.get("rollback_plan")),
            "effectiveness_score": score,
            "summary": statements[0] if statements else "Optimization execution completed; no comparable metrics changed.",
            "metrics": metrics,
            "statements": statements,
        }

    def _metric(self, name: str, before: Any, after: Any, unit: str, lower_is_better: bool) -> dict[str, Any]:
        if before is None or after is None:
            return {"name": name, "before": None, "after": None, "unit": unit, "delta": None, "score": 0}
        before_f = float(before)
        after_f = float(after)
        delta = after_f - before_f
        if before_f == 0:
            improvement = 0.0
        elif lower_is_better:
            improvement = ((before_f - after_f) / abs(before_f)) * 100
        else:
            improvement = ((after_f - before_f) / abs(before_f)) * 100
        return {
            "name": name,
            "before": round(before_f, 3),
            "after": round(after_f, 3),
            "unit": unit,
            "delta": round(delta, 3),
            "improvement_percent": round(improvement, 2),
            "score": max(-100, min(100, improvement)),
            "direction": "improved" if improvement > 0 else "regressed" if improvement < 0 else "unchanged",
        }

    def _network_total(self, snapshot: dict[str, Any]) -> float:
        network = snapshot.get("network", {})
        return float(network.get("bytes_recv_per_sec") or 0) + float(network.get("bytes_sent_per_sec") or 0)

    def _statements(self, metrics: list[dict[str, Any]]) -> list[str]:
        statements = []
        for metric in sorted(metrics, key=lambda item: item.get("improvement_percent") or 0, reverse=True):
            improvement = metric.get("improvement_percent") or 0
            if improvement > 1:
                statements.append(
                    f"AstraOS improved {metric['name'].lower()} by {round(improvement, 1)}% "
                    f"({metric['before']} -> {metric['after']} {metric['unit']})."
                )
        return statements or ["AstraOS captured before/after proof; measured impact was neutral for this run."]

    def _benchmark_statements(self, benchmark: dict[str, Any] | None) -> list[str]:
        if not benchmark:
            return []
        statements = []
        for metric in benchmark.get("metrics", []):
            before = metric.get("before")
            after = metric.get("after")
            if before in (None, 0) or after is None:
                continue
            improvement = ((float(before) - float(after)) / abs(float(before))) * 100
            if improvement > 0:
                statements.append(f"AstraOS reduced {metric.get('name', 'metric').lower()} by {round(improvement, 1)}% in recorded benchmark evidence.")
        return statements
