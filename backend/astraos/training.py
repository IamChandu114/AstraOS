from __future__ import annotations

import json
import pickle
import time
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestRegressor


class AdaptiveTrainingPipeline:
    """Train versioned models from real telemetry stored by AstraOS."""

    def __init__(self, model_dir: str | Path = "models") -> None:
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def train(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        rows = [self._features(item) for item in history if item]
        rows = [row for row in rows if row is not None]
        if len(rows) < 12:
            return {
                "timestamp": time.time(),
                "status": "insufficient_data",
                "sample_count": len(rows),
                "message": "Need at least 12 real telemetry samples to train adaptive models.",
            }
        data = np.array(rows, dtype=float)
        version = time.strftime("%Y%m%d-%H%M%S")

        anomaly = IsolationForest(contamination=0.08, random_state=42)
        anomaly.fit(data)

        clusters = KMeans(n_clusters=min(4, max(2, len(rows) // 8)), random_state=42, n_init=10)
        labels = clusters.fit_predict(data)

        forecast = RandomForestRegressor(n_estimators=64, random_state=42)
        forecast.fit(data[:-1], data[1:, 0])

        artifact = {
            "version": version,
            "created_at": time.time(),
            "sample_count": len(rows),
            "features": ["cpu", "memory", "swap", "temperature", "network_rx_kbps", "disk_kbps"],
            "cluster_counts": {str(label): int((labels == label).sum()) for label in set(labels)},
        }
        model_path = self.model_dir / f"astraos-model-{version}.pkl"
        meta_path = self.model_dir / f"astraos-model-{version}.json"
        with model_path.open("wb") as fh:
            pickle.dump({"anomaly": anomaly, "clusters": clusters, "forecast": forecast, "metadata": artifact}, fh)
        meta_path.write_text(json.dumps(artifact, indent=2))
        return {"timestamp": time.time(), "status": "trained", "artifact": artifact, "model_path": str(model_path), "metadata_path": str(meta_path)}

    def versions(self) -> list[dict[str, Any]]:
        versions = []
        for path in sorted(self.model_dir.glob("astraos-model-*.json"), reverse=True):
            try:
                versions.append(json.loads(path.read_text()))
            except Exception:
                continue
        return versions

    def _features(self, item: dict[str, Any]) -> list[float] | None:
        cpu = item.get("cpu", {}).get("usage_percent")
        memory = item.get("memory", {}).get("percent")
        if cpu is None or memory is None:
            return None
        disk = ((item.get("disk", {}).get("read_bytes_per_sec") or 0) + (item.get("disk", {}).get("write_bytes_per_sec") or 0)) / 1024
        return [
            float(cpu),
            float(memory),
            float(item.get("swap", {}).get("percent") or 0),
            float(item.get("thermal", {}).get("hottest_c") or 0),
            float(item.get("network", {}).get("bytes_recv_per_sec") or 0) / 1024,
            float(disk),
        ]
