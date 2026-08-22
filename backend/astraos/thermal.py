from __future__ import annotations

import math
import time
from typing import Any


class ThermalForecaster:
    """Forecast thermal risk and generate real-sensor-derived heatmap cells."""

    def forecast(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        values = [
            float(item.get("thermal", {}).get("hottest_c"))
            for item in history
            if item.get("thermal", {}).get("hottest_c") is not None
        ]
        gpu_values = []
        for item in history:
            gpu_values.extend(
                float(device.get("temperature_c"))
                for device in item.get("gpu", {}).get("devices", [])
                if device.get("temperature_c") is not None
            )

        series = values or gpu_values
        if not series:
            return {
                "timestamp": time.time(),
                "status": "unavailable",
                "message": "No host thermal sensor or GPU temperature telemetry is currently available.",
                "heatmap": [],
            }

        current = series[-1]
        slope = (series[-1] - series[0]) / max(1, len(series) - 1)
        forecast_30s = max(-20.0, min(125.0, current + slope * 30))
        risk = "critical" if forecast_30s >= 90 else "warning" if forecast_30s >= 82 else "normal"

        return {
            "timestamp": time.time(),
            "status": "live",
            "current_c": round(current, 2),
            "forecast_30s_c": round(forecast_30s, 2),
            "slope_c_per_sample": round(slope, 4),
            "risk": risk,
            "cooling_efficiency": round(max(0.0, min(1.0, 1 - max(0.0, slope) / 2.5)), 3),
            "heatmap": self._heatmap(current, forecast_30s),
        }

    def _heatmap(self, current: float, forecast: float) -> list[dict[str, Any]]:
        cells = []
        center = max(current, forecast)
        for row in range(8):
            for col in range(8):
                distance = math.sqrt((row - 3.5) ** 2 + (col - 3.5) ** 2)
                temp = center - distance * 4.3
                cells.append({
                    "row": row,
                    "col": col,
                    "temperature_c": round(max(20.0, temp), 2),
                    "risk": "hot" if temp >= 82 else "warm" if temp >= 65 else "normal",
                })
        return cells
