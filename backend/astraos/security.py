from __future__ import annotations

import re
import time
from typing import Any

from backend.astraos.process_filters import is_protected_process


class SecurityAnalyzer:
    """AI-adjacent behavioral security checks from real process/network telemetry."""

    SUSPICIOUS_NAMES = {"mimikatz", "xmrig", "miner", "ncat", "nc", "netcat", "powershell", "curl", "wget"}

    def analyze(self, snapshot: dict[str, Any], prediction: dict[str, Any] | None = None) -> dict[str, Any]:
        alerts = []
        for proc in snapshot.get("processes", {}).get("top", [])[:30]:
            if is_protected_process(proc):
                continue
            name = str(proc.get("name") or "").lower()
            cpu = float(proc.get("cpu_percent") or 0)
            if self._matches_suspicious_name(name) and cpu > 15:
                alerts.append({"type": "suspicious_process_resource_use", "process": proc, "severity": "high"})
            if cpu > 95:
                alerts.append({"type": "extreme_cpu_process", "process": proc, "severity": "medium"})

        rx = float(snapshot.get("network", {}).get("bytes_recv_per_sec") or 0)
        tx = float(snapshot.get("network", {}).get("bytes_sent_per_sec") or 0)
        if rx + tx > 50_000_000:
            alerts.append({"type": "abnormal_network_volume", "bytes_per_sec": rx + tx, "severity": "medium"})
        if prediction and prediction.get("anomaly", {}).get("is_anomaly"):
            alerts.append({"type": "ai_resource_anomaly", "score": prediction.get("anomaly", {}).get("score"), "severity": "medium"})

        score = min(100, sum(40 if alert["severity"] == "high" else 20 for alert in alerts))
        return {
            "timestamp": time.time(),
            "risk_score": score,
            "risk_level": "high" if score >= 70 else "medium" if score >= 30 else "low",
            "alerts": alerts,
        }

    def _matches_suspicious_name(self, name: str) -> bool:
        base = name.replace("\\", "/").rsplit("/", 1)[-1]
        stem = base.removesuffix(".exe")
        if stem in self.SUSPICIOUS_NAMES:
            return True
        tokens = {token for token in re.split(r"[^a-z0-9]+", stem) if token}
        if tokens.intersection(self.SUSPICIOUS_NAMES - {"nc"}):
            return True
        return "miner" in stem or stem.startswith("mimikatz")
