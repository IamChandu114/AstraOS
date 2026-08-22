#!/usr/bin/env python3
"""Thermal prediction and mitigation engine for AstraOS."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ThermalState:
    cpu_temp_c: float
    gpu_temp_c: float
    fan_percent: float
    cpu_load: float
    gpu_load: float


def analyze(state: ThermalState) -> dict:
    hotspot = "GPU" if state.gpu_temp_c - state.cpu_temp_c > 5 else "CPU"
    predicted_peak = max(state.cpu_temp_c + state.cpu_load * 0.07, state.gpu_temp_c + state.gpu_load * 0.08)
    actions = []

    if predicted_peak >= 90:
        actions.extend([
            "migrate_gpu_workload_to_cpu",
            "reduce_gpu_power_limit_20_percent",
            "increase_fan_curve_aggressiveness",
        ])
    elif predicted_peak >= 82:
        actions.extend(["rebalance_threads", "defer_background_indexing"])
    else:
        actions.append("observe")

    return {
        "hotspot": hotspot,
        "predicted_peak_c": round(predicted_peak, 2),
        "thermal_overload_predicted": predicted_peak >= 88,
        "actions": actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path)
    args = parser.parse_args()
    if args.state:
        payload = json.loads(args.state.read_text())
        state = ThermalState(**payload)
    else:
        state = ThermalState(cpu_temp_c=84, gpu_temp_c=88, fan_percent=62, cpu_load=82, gpu_load=76)
    print(json.dumps({"thermal": asdict(state), "analysis": analyze(state)}, indent=2))


if __name__ == "__main__":
    main()
