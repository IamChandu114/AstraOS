from __future__ import annotations

import time
from typing import Any


class DigitalTwin:
    """Predict future infrastructure state from real recent telemetry."""

    def project(self, history: list[dict[str, Any]], horizon_seconds: int = 60) -> dict[str, Any]:
        horizon_seconds = max(5, min(horizon_seconds, 600))
        if len(history) < 2:
            return {"timestamp": time.time(), "status": "warming_up", "states": []}

        cpu = self._values(history, ("cpu", "usage_percent"))
        memory = self._values(history, ("memory", "percent"))
        temp = self._values(history, ("thermal", "hottest_c"))
        states = []
        for step in range(5, horizon_seconds + 1, 5):
            state = {
                "t_plus_seconds": step,
                "cpu_percent": self._forecast(cpu, step),
                "memory_percent": self._forecast(memory, step),
                "temperature_c": self._forecast(temp, step) if temp else None,
            }
            state["risk"] = self._risk(state)
            states.append(state)
        return {
            "timestamp": time.time(),
            "status": "live",
            "horizon_seconds": horizon_seconds,
            "states": states,
            "recommended_strategy": self._strategy(states),
        }

    def _values(self, history: list[dict[str, Any]], path: tuple[str, ...]) -> list[float]:
        values = []
        for item in history:
            current: Any = item
            for key in path:
                current = current.get(key) if isinstance(current, dict) else None
            if current is not None:
                values.append(float(current))
        return values

    def _forecast(self, values: list[float], seconds: int) -> float | None:
        if not values:
            return None
        if len(values) == 1:
            return round(values[-1], 2)
        slope = (values[-1] - values[0]) / max(1, len(values) - 1)
        value = values[-1] + slope * (seconds / 5)
        return round(max(0.0, min(125.0, value)), 2)

    def _risk(self, state: dict[str, Any]) -> str:
        if (state.get("cpu_percent") or 0) >= 90 or (state.get("memory_percent") or 0) >= 90 or (state.get("temperature_c") or 0) >= 90:
            return "critical"
        if (state.get("cpu_percent") or 0) >= 80 or (state.get("memory_percent") or 0) >= 82 or (state.get("temperature_c") or 0) >= 82:
            return "warning"
        return "normal"

    def _strategy(self, states: list[dict[str, Any]]) -> str:
        if any(state["risk"] == "critical" for state in states):
            return "preemptive_rebalance_and_throttle"
        if any(state["risk"] == "warning" for state in states):
            return "watch_and_prepare_optimization"
        return "observe"
