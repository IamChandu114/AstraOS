#!/usr/bin/env python3
"""AstraOS AI workload prediction engine.

The module prefers PyTorch and scikit-learn when installed, but the demo path
keeps working with the Python standard library so the repository is portable.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List

try:
    import torch
    from torch import nn
except Exception:  # pragma: no cover - optional dependency
    torch = None
    nn = object

try:
    from sklearn.ensemble import IsolationForest, RandomForestRegressor
except Exception:  # pragma: no cover - optional dependency
    IsolationForest = None
    RandomForestRegressor = None


@dataclass
class Metrics:
    timestamp: float
    cpu_usage: float
    ram_usage: float
    temperature_c: float
    power_watts: float
    network_kbps: float
    inference_fps: float


@dataclass
class Prediction:
    cpu_spike_probability: float
    predicted_cpu_18s: float
    predicted_temperature_c: float
    memory_anomaly_score: float
    inefficient_process_score: float
    action: str
    confidence: float


if torch is not None:
    class WorkloadLSTM(nn.Module):
        def __init__(self, input_size: int = 6, hidden_size: int = 32) -> None:
            super().__init__()
            self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
            self.head = nn.Sequential(nn.Linear(hidden_size, 16), nn.ReLU(), nn.Linear(16, 2))

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.head(out[:, -1, :])
else:
    class WorkloadLSTM:  # type: ignore[no-redef]
        pass


class AstraPredictor:
    def __init__(self) -> None:
        self.rf = RandomForestRegressor(n_estimators=40, random_state=7) if RandomForestRegressor else None
        self.anomaly = IsolationForest(contamination=0.08, random_state=7) if IsolationForest else None
        self.is_fitted = False

    def fit(self, history: List[Metrics]) -> None:
        if len(history) < 8 or not self.rf:
            return
        x = [self._features(m) for m in history[:-1]]
        y = [[m.cpu_usage, m.temperature_c] for m in history[1:]]
        self.rf.fit(x, y)
        self.is_fitted = True
        if self.anomaly:
            self.anomaly.fit(x)

    def predict(self, history: List[Metrics]) -> Prediction:
        latest = history[-1]
        trend_cpu = self._trend([m.cpu_usage for m in history[-8:]])
        trend_temp = self._trend([m.temperature_c for m in history[-8:]])

        if self.rf is not None and self.is_fitted:
            pred_cpu, pred_temp = self.rf.predict([self._features(latest)])[0]
        else:
            pred_cpu = min(100.0, latest.cpu_usage + trend_cpu * 1.35)
            pred_temp = min(105.0, latest.temperature_c + trend_temp * 0.55 + max(0.0, latest.cpu_usage - 75.0) * 0.08)

        cpu_prob = self._sigmoid((pred_cpu - 82.0) / 8.0)
        memory_anomaly = self._memory_anomaly(history)
        inefficient = self._inefficiency_score(latest)

        thermal_risk = pred_temp >= 88.0
        cpu_risk = cpu_prob > 0.65
        mem_risk = memory_anomaly > 0.70

        if thermal_risk:
            action = "THERMAL_MIGRATION"
        elif cpu_risk:
            action = "CPU_REBALANCE"
        elif mem_risk:
            action = "MEMORY_COMPRESSION"
        else:
            action = "OBSERVE"

        confidence = min(0.98, 0.52 + max(cpu_prob, memory_anomaly, self._sigmoid((pred_temp - 78.0) / 8.0)) * 0.42)
        return Prediction(
            cpu_spike_probability=round(cpu_prob, 3),
            predicted_cpu_18s=round(pred_cpu, 2),
            predicted_temperature_c=round(pred_temp, 2),
            memory_anomaly_score=round(memory_anomaly, 3),
            inefficient_process_score=round(inefficient, 3),
            action=action,
            confidence=round(confidence, 3),
        )

    @staticmethod
    def _features(m: Metrics) -> List[float]:
        return [m.cpu_usage, m.ram_usage, m.temperature_c, m.power_watts, m.network_kbps, m.inference_fps]

    @staticmethod
    def _trend(values: Iterable[float]) -> float:
        series = list(values)
        if len(series) < 2:
            return 0.0
        return (series[-1] - series[0]) / max(1, len(series) - 1)

    @staticmethod
    def _sigmoid(value: float) -> float:
        return 1.0 / (1.0 + math.exp(-value))

    @staticmethod
    def _memory_anomaly(history: List[Metrics]) -> float:
        ram = [m.ram_usage for m in history[-12:]]
        if len(ram) < 4:
            return 0.0
        stdev = statistics.pstdev(ram) or 1.0
        z = abs(ram[-1] - statistics.mean(ram)) / stdev
        return min(1.0, z / 3.0)

    @staticmethod
    def _inefficiency_score(m: Metrics) -> float:
        heat_penalty = max(0.0, m.temperature_c - 75.0) / 25.0
        perf_penalty = max(0.0, 55.0 - m.inference_fps) / 55.0
        power_penalty = max(0.0, m.power_watts - 22.0) / 18.0
        return min(1.0, 0.38 * heat_penalty + 0.34 * perf_penalty + 0.28 * power_penalty)


class ReinforcementPolicy:
    """Lightweight policy scorer for optimization actions."""

    ACTIONS = ["OBSERVE", "CPU_REBALANCE", "THERMAL_MIGRATION", "MEMORY_COMPRESSION", "EDGE_OFFLOAD"]

    def score(self, metrics: Metrics, prediction: Prediction) -> dict:
        reward = {
            "OBSERVE": 0.2,
            "CPU_REBALANCE": prediction.cpu_spike_probability * 0.9 - metrics.power_watts / 120.0,
            "THERMAL_MIGRATION": max(0.0, prediction.predicted_temperature_c - 78.0) / 18.0,
            "MEMORY_COMPRESSION": prediction.memory_anomaly_score * 0.8,
            "EDGE_OFFLOAD": max(0.0, metrics.cpu_usage - 70.0) / 35.0 + max(0.0, 50.0 - metrics.inference_fps) / 80.0,
        }
        return dict(sorted(reward.items(), key=lambda item: item[1], reverse=True))


def synthetic_metrics(steps: int) -> List[Metrics]:
    output = []
    for i in range(steps):
        wave = math.sin(i / 4.0) * 8
        cpu = min(98, 42 + i * 1.8 + wave + random.uniform(-3, 3))
        temp = min(96, 48 + i * 1.25 + wave * 0.45 + random.uniform(-1.6, 1.6))
        ram = min(94, 48 + i * 0.75 + random.uniform(-2.0, 2.0))
        power = 14 + cpu * 0.19 + random.uniform(-1.2, 1.2)
        fps = max(25, 72 - cpu * 0.32 + random.uniform(-2.5, 2.5))
        output.append(Metrics(time.time() + i, cpu, ram, temp, power, 900 + cpu * 7, fps))
    return output


def load_metrics(path: Path) -> List[Metrics]:
    raw = json.loads(path.read_text())
    if isinstance(raw, dict):
        raw = raw.get("metrics", [])
    return [Metrics(**item) for item in raw]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--steps", type=int, default=24)
    args = parser.parse_args()

    history = load_metrics(args.metrics) if args.metrics else synthetic_metrics(args.steps)
    predictor = AstraPredictor()
    predictor.fit(history)
    prediction = predictor.predict(history)
    policy = ReinforcementPolicy().score(history[-1], prediction)

    result = {"prediction": asdict(prediction), "policy_rank": policy}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
