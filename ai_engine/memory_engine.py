#!/usr/bin/env python3
"""Adaptive memory optimization engine for AstraOS."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict


@dataclass
class MemoryState:
    total_gb: float
    used_gb: float
    cache_gb: float
    inactive_gb: float
    swap_gb: float


def optimize(state: MemoryState) -> dict:
    pressure = state.used_gb / state.total_gb
    recovered = 0.0
    actions = []

    if pressure > 0.82:
        recovered += min(state.inactive_gb * 0.45, 1.2)
        actions.append("compress_inactive_memory_blocks")
    if state.cache_gb > 1.0 and pressure > 0.72:
        recovered += min(state.cache_gb * 0.25, 0.8)
        actions.append("trim_low_value_page_cache")
    if state.swap_gb > 0.5:
        actions.append("protect_foreground_working_sets")
    if not actions:
        actions.append("observe")

    return {
        "memory_pressure": round(pressure, 3),
        "recovered_gb_estimate": round(recovered, 2),
        "actions": actions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--total", type=float, default=8.0)
    parser.add_argument("--used", type=float, default=7.1)
    parser.add_argument("--cache", type=float, default=1.8)
    parser.add_argument("--inactive", type=float, default=2.7)
    parser.add_argument("--swap", type=float, default=0.8)
    args = parser.parse_args()
    state = MemoryState(args.total, args.used, args.cache, args.inactive, args.swap)
    print(json.dumps({"memory": asdict(state), "optimization": optimize(state)}, indent=2))


if __name__ == "__main__":
    main()
