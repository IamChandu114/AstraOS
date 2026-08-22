from __future__ import annotations

import time
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestRegressor


def _series(history: list[dict[str, Any]], path: tuple[str, ...]) -> list[float]:
    values = []
    for item in history:
        current: Any = item
        for key in path:
            current = current.get(key) if isinstance(current, dict) else None
        if current is not None:
            values.append(float(current))
    return values


def _linear_model(values: list[float]) -> tuple[float, float] | None:
    if len(values) < 2:
        return None
    x = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x, np.array(values, dtype=float), 1)
    return float(slope), float(intercept)


def _trend(values: list[float], horizon: float = 6.0) -> float | None:
    if len(values) < 2:
        return values[-1] if values else None
    model = _linear_model(values)
    if not model:
        return values[-1] if values else None
    slope, intercept = model
    return float(intercept + slope * (len(values) - 1 + horizon))


class RealTelemetryPredictor:
    """Prediction engine trained only on observed telemetry from this host."""

    def predict(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        if not history:
            return {
                "timestamp": time.time(),
                "status": "insufficient_live_telemetry",
                "message": "Waiting for real telemetry samples.",
            }

        latest = history[-1]
        cpu_values = _series(history[-120:], ("cpu", "usage_percent"))
        temp_values = _series(history[-120:], ("thermal", "hottest_c"))
        memory_values = _series(history[-120:], ("memory", "percent"))
        power_values = self._power_series(history[-120:])

        prediction = {
            "timestamp": time.time(),
            "status": "live",
            "sample_count": len(history),
            "cpu_spike": self._forecast("cpu", cpu_values, threshold=82.0, exhaustion_threshold=96.0),
            "thermal": self._forecast("temperature", temp_values, threshold=85.0),
            "memory_pressure": self._forecast("memory", memory_values, threshold=78.0, exhaustion_threshold=92.0),
            "power": self._forecast("power", power_values, threshold=28.0),
            "anomaly": self._anomaly(history[-240:]),
            "workload_class": self._classify(latest),
        }
        prediction["recommendations"] = self._recommend(prediction)
        return prediction

    def _forecast(self, name: str, values: list[float], threshold: float, exhaustion_threshold: float | None = None) -> dict[str, Any]:
        exhaustion_threshold = exhaustion_threshold or threshold * 1.08
        current = values[-1] if values else None
        if current is None:
            return {"metric": name, "current": current, "forecast_6s": None, "risk": "unknown", "confidence": 0.0, "reasoning": ["No live samples for this metric."]}
        slope = 0.0
        if len(values) >= 2:
            model = _linear_model(values)
            slope = model[0] if model else 0.0
        if len(values) < 12:
            risk = "critical" if current >= exhaustion_threshold else "warning" if current >= threshold else "normal"
            risk_score = self._risk_score(current, current, threshold, exhaustion_threshold, slope)
            eta = self._eta_seconds(current, slope, exhaustion_threshold)
            return {
                "metric": name,
                "current": round(current, 2),
                "forecast_6s": round(current, 2),
                "forecast_60s": round(current, 2),
                "forecast_5m": round(current, 2),
                "delta": 0.0,
                "threshold": threshold,
                "exhaustion_threshold": exhaustion_threshold,
                "risk": risk,
                "risk_score": risk_score,
                "confidence": round(0.2 + min(0.2, len(values) / 30), 3),
                "status": "warming_up",
                **self._failure_window(eta),
                "reasoning": [
                    f"Only {len(values)} live samples are available; current {name} is {round(current, 2)}.",
                    f"Warning threshold is {threshold}; exhaustion threshold is {exhaustion_threshold}.",
                ],
            }
        forecast = _trend(values, 6)
        if forecast is None:
            return {"metric": name, "current": current, "forecast_6s": forecast, "risk": "unknown", "confidence": 0.0}
        forecast = self._clamp_forecast(name, forecast)
        forecast_60s = self._clamp_forecast(name, _trend(values, 60) or forecast)
        forecast_5m = self._clamp_forecast(name, _trend(values, 300) or forecast_60s)
        delta = forecast - current
        risk = self._risk(current, forecast_60s, forecast_5m, threshold, exhaustion_threshold, slope)
        risk_score = self._risk_score(current, max(forecast, forecast_60s, forecast_5m), threshold, exhaustion_threshold, slope)
        confidence = min(0.95, 0.35 + min(0.6, len(values) / 180) + min(0.15, abs(forecast_60s - current) / max(1.0, threshold)))
        if len(values) >= 24:
            try:
                x = np.array([[i] for i in range(len(values) - 1)], dtype=float)
                y = np.array(values[1:], dtype=float)
                model = RandomForestRegressor(n_estimators=32, random_state=17)
                model.fit(x, y)
                ml_forecast = self._clamp_forecast(name, float(model.predict([[len(values) + 6]])[0]))
                forecast = max(forecast, ml_forecast) if slope > 0 else ml_forecast
                risk = self._risk(current, forecast_60s, forecast_5m, threshold, exhaustion_threshold, slope)
                confidence = min(0.96, confidence + 0.12)
            except Exception:
                pass
        eta = self._eta_seconds(current, slope, exhaustion_threshold)
        return {
            "metric": name,
            "current": round(current, 2),
            "forecast_6s": round(forecast, 2),
            "forecast_60s": round(forecast_60s, 2),
            "forecast_5m": round(forecast_5m, 2),
            "delta": round(forecast - current, 2),
            "delta_60s": round(forecast_60s - current, 2),
            "threshold": threshold,
            "exhaustion_threshold": exhaustion_threshold,
            "risk": risk,
            "risk_score": risk_score,
            "confidence": round(confidence, 3),
            "trend_per_sample": round(slope, 4),
            **self._failure_window(eta),
            "reasoning": [
                f"Current {name} is {round(current, 2)} and 60-second forecast is {round(forecast_60s, 2)}.",
                f"Observed trend is {round(slope, 4)} percentage points per sample.",
                f"Risk score is {risk_score}/100 against exhaustion threshold {exhaustion_threshold}.",
            ],
        }

    def _risk(self, current: float, forecast_60s: float, forecast_5m: float, threshold: float, exhaustion_threshold: float, slope: float) -> str:
        if current >= exhaustion_threshold or forecast_60s >= exhaustion_threshold:
            return "critical"
        if current >= threshold or forecast_60s >= threshold or forecast_5m >= exhaustion_threshold:
            return "warning"
        if slope > 0.08 and forecast_5m >= threshold:
            return "warning"
        return "normal"

    def _risk_score(self, current: float, forecast: float, threshold: float, exhaustion_threshold: float, slope: float) -> int:
        pressure = max(current, forecast)
        threshold_span = max(1.0, exhaustion_threshold - threshold)
        if pressure < threshold:
            base = (pressure / max(1.0, threshold)) * 58
        else:
            base = 60 + ((pressure - threshold) / threshold_span) * 35
        trend_bonus = max(0.0, min(10.0, slope * 18))
        return int(max(0, min(100, round(base + trend_bonus))))

    def _eta_seconds(self, current: float, slope: float, exhaustion_threshold: float) -> float | None:
        if current >= exhaustion_threshold:
            return 0.0
        if slope <= 0:
            return None
        return max(1.0, (exhaustion_threshold - current) / slope)

    def _failure_window(self, eta_seconds: float | None) -> dict[str, Any]:
        if eta_seconds is None:
            return {
                "time_to_threshold_seconds": None,
                "expected_failure_time": None,
                "expected_failure_label": None,
                "failure_window": "No exhaustion window projected from current trend.",
            }
        expected = time.time() + eta_seconds
        return {
            "time_to_threshold_seconds": round(eta_seconds, 1),
            "expected_failure_time": expected,
            "expected_failure_label": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expected)),
            "failure_window": "now" if eta_seconds == 0 else f"within {max(1, round(eta_seconds / 60))} minutes",
        }

    @staticmethod
    def _clamp_forecast(name: str, value: float) -> float:
        if name in {"cpu", "memory"}:
            return max(0.0, min(100.0, value))
        if name == "temperature":
            return max(-20.0, min(125.0, value))
        return max(0.0, value)

    def _anomaly(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        rows = []
        for item in history:
            rows.append([
                float(item.get("cpu", {}).get("usage_percent") or 0),
                float(item.get("memory", {}).get("percent") or 0),
                float(item.get("swap", {}).get("percent") or 0),
                float(item.get("thermal", {}).get("hottest_c") or 0),
                float(item.get("network", {}).get("bytes_recv_per_sec") or 0),
            ])
        if len(rows) < 20:
            return {"score": 0.0, "is_anomaly": False, "status": "warming_up"}
        model = IsolationForest(contamination=0.08, random_state=23)
        model.fit(rows[:-1])
        score = float(-model.decision_function([rows[-1]])[0])
        is_anomaly = bool(model.predict([rows[-1]])[0] == -1)
        return {"score": round(max(0.0, score), 4), "is_anomaly": is_anomaly, "status": "live"}

    def _classify(self, snapshot: dict[str, Any]) -> str:
        cpu = float(snapshot.get("cpu", {}).get("usage_percent") or 0)
        memory = float(snapshot.get("memory", {}).get("percent") or 0)
        net = float(snapshot.get("network", {}).get("bytes_recv_per_sec") or 0)
        disk = float(snapshot.get("disk", {}).get("read_bytes_per_sec") or 0) + float(snapshot.get("disk", {}).get("write_bytes_per_sec") or 0)
        if cpu > 70 and memory > 70:
            return "compute_memory_pressure"
        if cpu > 70:
            return "compute_bound"
        if memory > 78:
            return "memory_bound"
        if net > 5_000_000:
            return "network_bound"
        if disk > 20_000_000:
            return "io_bound"
        return "balanced"

    def _power_series(self, history: list[dict[str, Any]]) -> list[float]:
        values = []
        for item in history:
            gpu_devices = item.get("gpu", {}).get("devices", [])
            gpu_power = sum(float(device.get("power_watts") or 0) for device in gpu_devices)
            cpu_proxy = float(item.get("cpu", {}).get("usage_percent") or 0) * 0.22
            values.append(gpu_power + cpu_proxy)
        return values

    def _recommend(self, prediction: dict[str, Any]) -> list[str]:
        recs = []
        if prediction["cpu_spike"]["risk"] in {"warning", "critical"}:
            recs.append("rebalance_cpu_affinity")
        if prediction["thermal"]["risk"] in {"warning", "critical"}:
            recs.append("reduce_thermal_pressure")
        if prediction["memory_pressure"]["risk"] in {"warning", "critical"}:
            recs.append("trim_cache_and_detect_leaks")
        if prediction["anomaly"].get("is_anomaly"):
            recs.append("investigate_resource_anomaly")
        return recs or ["observe"]
