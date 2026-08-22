#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from astraos.collector import TelemetryCollector
from astraos.policy import OptimizationPolicy
from astraos.prediction import RealTelemetryPredictor
from astraos.storage import TelemetryStore


def scheduling_latency(samples: int = 250) -> dict:
    latencies = []
    for _ in range(samples):
        start = time.perf_counter()
        time.sleep(0.001)
        latencies.append((time.perf_counter() - start) * 1000)
    return {
        "median_ms": round(statistics.median(latencies), 4),
        "p95_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 4),
        "max_ms": round(max(latencies), 4),
    }


def collect_window(seconds: int) -> list[dict]:
    collector = TelemetryCollector()
    history = []
    for _ in range(seconds):
        history.append(collector.collect())
        time.sleep(1)
    return history


def summarize(history: list[dict], latency: dict) -> dict:
    latest = history[-1]
    temps = [item.get("thermal", {}).get("hottest_c") for item in history if item.get("thermal", {}).get("hottest_c") is not None]
    return {
        "cpu_percent_avg": round(statistics.mean(item["cpu"]["usage_percent"] for item in history), 2),
        "memory_percent_avg": round(statistics.mean(item["memory"]["percent"] for item in history), 2),
        "thermal_peak_c": round(max(temps), 2) if temps else None,
        "processes": latest["processes"]["total"],
        "latency_median_ms": latency["median_ms"],
        "latency_p95_ms": latency["p95_ms"],
        "disk_kbps": round((((latest["disk"].get("read_bytes_per_sec") or 0) + (latest["disk"].get("write_bytes_per_sec") or 0)) / 1024), 2),
        "network_rx_kbps": round((latest["network"].get("bytes_recv_per_sec") or 0) / 1024, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=8)
    parser.add_argument("--apply", action="store_true", help="Apply real optimization actions if ASTRAOS_ENABLE_APPLY=1 is set.")
    parser.add_argument("--out-json", type=Path, default=ROOT / "benchmarks" / "real_benchmark.json")
    parser.add_argument("--out-csv", type=Path, default=ROOT / "benchmarks" / "real_benchmark.csv")
    args = parser.parse_args()

    baseline_history = collect_window(args.seconds)
    baseline_latency = scheduling_latency()

    prediction = RealTelemetryPredictor().predict(baseline_history)
    plan = OptimizationPolicy().plan(baseline_history[-1], prediction)
    applied = OptimizationPolicy().apply(plan) if args.apply else {"mode": "plan_only", "results": []}

    after_history = collect_window(args.seconds)
    after_latency = scheduling_latency()

    before = summarize(baseline_history, baseline_latency)
    after = summarize(after_history, after_latency)
    report = {
        "timestamp": time.time(),
        "status": "real_benchmark",
        "apply_requested": args.apply,
        "optimization_plan": plan,
        "optimization_result": applied,
        "before": before,
        "after": after,
        "metrics": [
            {"name": "CPU Latency p95", "unit": "ms", "before": before["latency_p95_ms"], "after": after["latency_p95_ms"]},
            {"name": "CPU Usage Avg", "unit": "%", "before": before["cpu_percent_avg"], "after": after["cpu_percent_avg"]},
            {"name": "Memory Usage Avg", "unit": "%", "before": before["memory_percent_avg"], "after": after["memory_percent_avg"]},
            {"name": "Thermal Peak", "unit": "C", "before": before["thermal_peak_c"], "after": after["thermal_peak_c"]},
            {"name": "Network RX", "unit": "KB/s", "before": before["network_rx_kbps"], "after": after["network_rx_kbps"]},
        ],
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2))
    with args.out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "unit", "before", "after"])
        writer.writeheader()
        writer.writerows(report["metrics"])

    TelemetryStore().write_benchmark(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
