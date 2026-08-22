from __future__ import annotations

import time
from typing import Any


class PredictiveAlertEngine:
    """Future-oriented alerts from live telemetry trends and AI forecasts."""

    def generate(
        self,
        history: list[dict[str, Any]],
        prediction: dict[str, Any] | None,
        root_cause: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = time.time()
        latest = history[-1] if history else None
        if not latest:
            return {
                "timestamp": now,
                "status": "warming_up",
                "reliability_index": {"score": 0, "trend": "warming"},
                "alerts": [],
                "timeline": [],
                "executive_summary": "AstraOS is collecting enough telemetry to generate predictive operations alerts.",
            }

        alerts = []
        for resource, config in self._resources().items():
            current = self._current_value(latest, resource)
            forecast_data = self._forecast_data(prediction, resource)
            forecast = forecast_data.get("forecast")
            if current is None and forecast is None:
                continue
            value = forecast if forecast is not None else current
            threshold = float(forecast_data.get("threshold") or config["threshold"])
            trend = self._trend(history, resource)
            risk = self._risk(value, threshold, trend, forecast_data)
            if risk in {"warning", "critical", "predictive"}:
                minutes = self._eta_minutes(current or value, value, threshold, trend, forecast_data)
                alerts.append(self._alert(resource, current, value, threshold, minutes, risk, prediction, root_cause, forecast_data))
        process_alert = self._process_instability_alert(history, latest, root_cause)
        if process_alert:
            alerts.append(process_alert)

        reliability = self.reliability_index(latest, prediction)
        timeline = self.timeline(history, prediction, alerts)
        prevention = self.prevention_counter(alerts, reliability)
        return {
            "timestamp": now,
            "status": "live",
            "reliability_index": reliability,
            "alerts": alerts,
            "timeline": timeline,
            "prevention_counter": prevention,
            "copilot": self.copilot(latest, alerts, root_cause),
            "demo_flow": self.demo_flow(alerts, reliability, prevention),
            "executive_summary": self.executive_summary(alerts, reliability, prevention),
        }

    def reliability_index(self, snapshot: dict[str, Any], prediction: dict[str, Any] | None = None) -> dict[str, Any]:
        cpu = float(snapshot.get("cpu", {}).get("usage_percent") or 0)
        memory = float(snapshot.get("memory", {}).get("percent") or 0)
        disk = float(snapshot.get("disk", {}).get("root_percent") or 0)
        temp = snapshot.get("thermal", {}).get("hottest_c")
        net = (float(snapshot.get("network", {}).get("bytes_recv_per_sec") or 0) + float(snapshot.get("network", {}).get("bytes_sent_per_sec") or 0)) / 1024 / 1024
        penalties = [
            max(0, cpu - 55) * 0.45,
            max(0, memory - 60) * 0.5,
            max(0, disk - 70) * 0.35,
            max(0, (float(temp) if temp is not None else 45) - 70) * 0.7,
            max(0, net - 20) * 0.35,
        ]
        if prediction:
            for key in ("cpu_spike", "memory_pressure", "thermal", "power"):
                risk = prediction.get(key, {}).get("risk")
                risk_score = float(prediction.get(key, {}).get("risk_score") or 0)
                penalties.append(max(0, risk_score - 55) * 0.22)
                if risk == "critical":
                    penalties.append(12)
                elif risk == "warning":
                    penalties.append(6)
        score = round(max(0, min(100, 100 - sum(penalties))), 1)
        trend = "improving" if score >= 85 else "watch" if score >= 65 else "degrading"
        return {"score": score, "trend": trend}

    def timeline(self, history: list[dict[str, Any]], prediction: dict[str, Any] | None, alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        latest = history[-1] if history else {}
        now = time.time()
        primary = alerts[0] if alerts else None
        resource = primary["affected_resource"] if primary else "cpu"
        current = self._current_value(latest, resource) or 0
        predicted = primary["predicted_value"] if primary else current
        steps = []
        for index, pct in enumerate([0, 0.33, 0.66, 1.0]):
            value = current + (predicted - current) * pct
            steps.append({
                "timestamp": now + index * 300,
                "label": "NOW" if index == 0 else f"+{index * 5} min",
                "time": time.strftime("%H:%M:%S", time.localtime(now + index * 300)),
                "resource": resource,
                "value": round(value, 2),
                "risk_level": primary["risk_level"] if primary and index == 3 else "info",
                "confidence": primary["confidence_score"] if primary else 0.72,
                "trend": primary["trend_direction"] if primary else "stable",
            })
        if primary:
            steps.append({
                "timestamp": primary["expected_failure_time"],
                "label": "PREDICTED EVENT",
                "time": primary.get("expected_failure_label"),
                "resource": resource,
                "value": primary["predicted_value"],
                "risk_level": primary["risk_level"],
                "confidence": primary["confidence_score"],
                "trend": primary["trend_direction"],
            })
        return steps

    def prevention_counter(self, alerts: list[dict[str, Any]], reliability: dict[str, Any]) -> dict[str, Any]:
        critical = len([item for item in alerts if item["risk_level"] == "critical"])
        predictive = len([item for item in alerts if item["category"] == "PREDICTIVE"])
        prevented = max(0, critical * 12 + predictive * 6)
        savings = max(0, min(42, round((100 - float(reliability["score"])) * 0.35 + predictive * 4, 1)))
        return {
            "downtime_prevented_minutes": prevented,
            "downtime_prevented_label": f"{prevented // 60}h {prevented % 60}m",
            "incidents_avoided": critical + predictive,
            "optimization_savings_percent": savings,
        }

    def executive_summary(self, alerts: list[dict[str, Any]], reliability: dict[str, Any], prevention: dict[str, Any] | None = None) -> str:
        prevention = prevention or self.prevention_counter(alerts, reliability)
        critical = len([item for item in alerts if item["risk_level"] == "critical"])
        return (
            f"System reliability is {reliability['score']}/100 and trending {reliability['trend']}. "
            f"{len(alerts)} predictive alerts active, {critical} critical risks, "
            f"estimated downtime prevented: {prevention['downtime_prevented_label']}."
        )

    def copilot(self, snapshot: dict[str, Any], alerts: list[dict[str, Any]], root_cause: dict[str, Any] | None) -> dict[str, Any]:
        top = (snapshot.get("processes", {}).get("top") or [])[:4]
        contributors = [
            {
                "name": proc.get("name", "unknown"),
                "pid": proc.get("pid"),
                "cpu_percent": proc.get("cpu_percent", 0),
                "memory_percent": proc.get("memory_percent", 0),
            }
            for proc in top
        ]
        primary = alerts[0] if alerts else None
        fix = "Continue observing live telemetry"
        improvement = "No immediate optimization required"
        if primary and primary.get("recommended_actions"):
            fix = primary["recommended_actions"][0]["action"]
            improvement = primary["recommended_actions"][0]["expected_benefit"]
        return {
            "question": "Why is my server slow?",
            "answer": "Root cause found" if root_cause and root_cause.get("findings") else "Runtime is stable",
            "contributors": contributors,
            "recommended_fix": fix,
            "expected_improvement": improvement,
            "confidence": primary.get("confidence_score") if primary else 0.74,
        }

    def demo_flow(self, alerts: list[dict[str, Any]], reliability: dict[str, Any], prevention: dict[str, Any]) -> list[dict[str, Any]]:
        primary = alerts[0] if alerts else None
        return [
            {"stage": "Observe", "status": f"Reliability {reliability['score']}/100", "detail": "Live telemetry stream active."},
            {"stage": "Predict", "status": primary["title"] if primary else "No future failure predicted", "detail": primary.get("message") if primary else "Trend window is healthy."},
            {"stage": "Decide", "status": primary["why"][0] if primary else "No action required", "detail": f"Confidence {round(float(primary.get('confidence_score', 0)) * 100)}%" if primary else "Confidence 74%."},
            {"stage": "Act", "status": primary["recommended_actions"][0]["action"] if primary and primary.get("recommended_actions") else "Keep optimization plan ready", "detail": "Guarded apply mode protects host-changing actions."},
            {"stage": "Verify", "status": f"Downtime prevented {prevention['downtime_prevented_label']}", "detail": f"Incidents avoided {prevention['incidents_avoided']}."},
        ]

    def _alert(
        self,
        resource: str,
        current: float | None,
        predicted: float,
        threshold: float,
        eta_minutes: int,
        risk: str,
        prediction: dict[str, Any] | None,
        root_cause: dict[str, Any] | None,
        forecast_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = time.time()
        confidence = self._confidence(prediction, resource, risk)
        forecast_data = forecast_data or {}
        expected_failure = forecast_data.get("expected_failure_time") or now + eta_minutes * 60
        reasons = self._reasons(resource, current, predicted, root_cause, forecast_data)
        recommendations = self._recommendations(resource, current, predicted)
        alert_bucket = int(float(expected_failure) // 300)
        return {
            "alert_id": f"pred-{resource}-{alert_bucket}",
            "category": "PREDICTIVE",
            "risk_level": risk,
            "prediction_time": now,
            "expected_failure_time": expected_failure,
            "expected_failure_label": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expected_failure)),
            "time_remaining_minutes": eta_minutes,
            "confidence_score": confidence,
            "affected_resource": resource,
            "current_value": round(current, 2) if current is not None else None,
            "predicted_value": round(predicted, 2),
            "forecast_60s": forecast_data.get("forecast_60s"),
            "forecast_5m": forecast_data.get("forecast_5m"),
            "risk_score": forecast_data.get("risk_score"),
            "threshold": threshold,
            "trend_direction": "increasing" if predicted >= (current or predicted) else "stable",
            "title": f"Predicted {resource.replace('_', ' ')} risk in {eta_minutes} minutes",
            "message": f"{resource.replace('_', ' ').title()} expected to reach {round(predicted, 1)} near {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expected_failure))}.",
            "why": reasons,
            "recommended_actions": recommendations,
            "impact_simulation": self._simulate(resource, current or predicted, predicted, recommendations),
        }

    def _resources(self) -> dict[str, dict[str, float]]:
        return {
            "cpu": {"threshold": 90},
            "memory": {"threshold": 88},
            "thermal": {"threshold": 86},
            "disk": {"threshold": 90},
            "network": {"threshold": 40},
        }

    def _current_value(self, snapshot: dict[str, Any], resource: str) -> float | None:
        if resource == "cpu":
            return float(snapshot.get("cpu", {}).get("usage_percent") or 0)
        if resource == "memory":
            return float(snapshot.get("memory", {}).get("percent") or 0)
        if resource == "thermal":
            temp = snapshot.get("thermal", {}).get("hottest_c")
            return float(temp) if temp is not None else None
        if resource == "disk":
            return float(snapshot.get("disk", {}).get("root_percent") or 0)
        if resource == "network":
            return (float(snapshot.get("network", {}).get("bytes_recv_per_sec") or 0) + float(snapshot.get("network", {}).get("bytes_sent_per_sec") or 0)) / 1024 / 1024
        if resource == "process_instability":
            processes = self._candidate_processes(snapshot)
            if not processes:
                return 0.0
            top_cpu = max(float(proc.get("cpu_percent") or 0) for proc in processes)
            process_count = float(snapshot.get("processes", {}).get("total") or 0)
            return min(100.0, top_cpu + max(0.0, process_count - 180) * 0.08)
        return None

    def _forecast_data(self, prediction: dict[str, Any] | None, resource: str) -> dict[str, Any]:
        if not prediction:
            return {"forecast": None}
        mapping = {"cpu": "cpu_spike", "memory": "memory_pressure", "thermal": "thermal", "network": "power"}
        key = mapping.get(resource)
        if not key:
            return {"forecast": None}
        forecast = prediction.get(key, {})
        candidates = [
            forecast.get("forecast_6s"),
            forecast.get("forecast_60s"),
            forecast.get("forecast_5m"),
        ]
        numeric = [float(value) for value in candidates if value is not None]
        return {
            "forecast": max(numeric) if numeric else None,
            "forecast_60s": forecast.get("forecast_60s"),
            "forecast_5m": forecast.get("forecast_5m"),
            "threshold": forecast.get("threshold"),
            "risk": forecast.get("risk"),
            "risk_score": forecast.get("risk_score"),
            "confidence": forecast.get("confidence"),
            "expected_failure_time": forecast.get("expected_failure_time"),
            "time_to_threshold_seconds": forecast.get("time_to_threshold_seconds"),
            "reasoning": forecast.get("reasoning") or [],
        }

    def _trend(self, history: list[dict[str, Any]], resource: str) -> float:
        if len(history) < 3:
            return 0.0
        start = self._current_value(history[-min(12, len(history))], resource)
        end = self._current_value(history[-1], resource)
        if start is None or end is None:
            return 0.0
        return end - start

    def _risk(self, value: float, threshold: float, trend: float, forecast_data: dict[str, Any] | None = None) -> str:
        forecast_data = forecast_data or {}
        model_risk = forecast_data.get("risk")
        risk_score = float(forecast_data.get("risk_score") or 0)
        if model_risk == "critical" or risk_score >= 90:
            return "critical"
        if model_risk == "warning" or risk_score >= 72:
            return "warning"
        if value >= threshold:
            return "critical"
        if value >= threshold * 0.9:
            return "warning"
        if trend > 8 and value >= threshold * 0.7:
            return "predictive"
        return "info"

    def _eta_minutes(self, current: float, predicted: float, threshold: float, trend: float, forecast_data: dict[str, Any] | None = None) -> int:
        forecast_data = forecast_data or {}
        eta_seconds = forecast_data.get("time_to_threshold_seconds")
        if eta_seconds is not None:
            return max(1, min(240, int(float(eta_seconds) / 60) or 1))
        if predicted >= threshold:
            return max(1, min(30, int((threshold - current) / max(1, abs(predicted - current)) * 6) if predicted != current else 6))
        if trend > 0:
            return max(3, min(45, int((threshold - current) / max(1, trend) * 5)))
        return 15

    def _confidence(self, prediction: dict[str, Any] | None, resource: str, risk: str) -> float:
        mapping = {"cpu": "cpu_spike", "memory": "memory_pressure", "thermal": "thermal"}
        raw = prediction.get(mapping.get(resource, ""), {}).get("confidence") if prediction else None
        base = float(raw) if raw is not None else 0.78
        if risk == "critical":
            base += 0.08
        return round(max(0.5, min(0.98, base)), 3)

    def _reasons(self, resource: str, current: float | None, predicted: float, root_cause: dict[str, Any] | None, forecast_data: dict[str, Any] | None = None) -> list[str]:
        reasons = [f"{resource.replace('_', ' ').title()} trend is moving from {round(current or 0, 1)} to projected {round(predicted, 1)}."]
        reasons.extend((forecast_data or {}).get("reasoning") or [])
        if root_cause and root_cause.get("findings"):
            finding = root_cause["findings"][0]
            reasons.extend((finding.get("reasoning") or [])[:2])
        return reasons

    def _recommendations(self, resource: str, current: float | None, predicted: float) -> list[dict[str, Any]]:
        actions = {
            "cpu": [("Reduce high-CPU process priority", 22, 3, "Low"), ("Apply CPU affinity plan", 18, 4, "Medium")],
            "memory": [("Close or isolate memory-heavy process", 18, 4, "Low"), ("Run guarded cache reclaim recommendation", 12, 2, "Medium")],
            "thermal": [("Migrate sustained workload", 9, 5, "Low"), ("Reduce background CPU pressure", 12, 4, "Low")],
            "disk": [("Pause disk-heavy task", 20, 3, "Low"), ("Move temporary workload", 14, 5, "Medium")],
            "network": [("Throttle non-critical sync", 16, 3, "Low"), ("Move workload to healthier node", 20, 5, "Medium")],
            "process_instability": [("Reduce unstable process priority", 24, 3, "Low"), ("Isolate workload in guarded execution group", 18, 5, "Medium")],
        }
        return [
            {
                "action": action,
                "expected_benefit": f"{benefit}% reduction",
                "estimated_recovery_time": f"{minutes} minutes",
                "risk": risk,
            }
            for action, benefit, minutes, risk in actions.get(resource, [])
        ]

    def _simulate(self, resource: str, current: float, predicted: float, recommendations: list[dict[str, Any]]) -> dict[str, Any]:
        reduction = 0
        for rec in recommendations:
            reduction += float(str(rec["expected_benefit"]).split("%")[0])
        after = max(0, predicted - reduction)
        return {
            "current_state": round(current, 2),
            "predicted_state": round(predicted, 2),
            "after_optimization": round(after, 2),
            "confidence": 0.88 if recommendations else 0.7,
            "resource": resource,
        }

    def _process_instability_alert(
        self,
        history: list[dict[str, Any]],
        latest: dict[str, Any],
        root_cause: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        processes = self._candidate_processes(latest)
        if not processes:
            return None
        top = max(processes, key=lambda proc: float(proc.get("cpu_percent") or 0))
        top_cpu = float(top.get("cpu_percent") or 0)
        states = latest.get("processes", {}).get("states") or {}
        blocked = float(states.get("disk_sleep") or states.get("blocked") or 0)
        if top_cpu < 65 and blocked < 4:
            return None
        predicted = min(100.0, top_cpu + blocked * 3 + max(0, self._trend(history, "cpu")) * 0.5)
        alert = self._alert("process_instability", top_cpu, predicted, 85, 10, "predictive" if predicted < 85 else "warning", None, root_cause)
        alert["title"] = f"Process instability likely from {top.get('name', 'top process')}"
        alert["message"] = f"{top.get('name', 'A process')} is consuming {round(top_cpu, 1)}% CPU and may destabilize workload latency."
        alert["affected_process"] = {"name": top.get("name"), "pid": top.get("pid"), "cpu_percent": top_cpu}
        alert["why"].insert(0, f"Top process {top.get('name', 'unknown')} is consuming {round(top_cpu, 1)}% CPU.")
        return alert

    def _candidate_processes(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        ignored = {"system idle process", "system"}
        return [
            proc for proc in (snapshot.get("processes", {}).get("top") or [])
            if int(proc.get("pid") or 0) > 1 and str(proc.get("name") or "").lower() not in ignored
        ]
