#!/usr/bin/env python3
"""AstraOS intelligent CPU scheduler and optimization planner."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


@dataclass
class Process:
    pid: int
    name: str
    cpu: float
    memory: float
    state: str = "R"
    priority: int = 0


@dataclass
class Action:
    type: str
    target: str
    command: str
    reason: str
    risk: str = "low"


def load_processes(path: Path) -> List[Process]:
    raw = json.loads(path.read_text())
    return [Process(**item) for item in raw.get("processes", [])]


def available_cores() -> List[int]:
    return list(range(os.cpu_count() or 1))


def plan(processes: List[Process]) -> List[Action]:
    cores = available_cores()
    perf_cores = cores[: max(1, len(cores) // 2)]
    eff_cores = cores[max(1, len(cores) // 2) :] or perf_cores
    actions: List[Action] = []

    heavy = sorted([p for p in processes if p.cpu >= 35], key=lambda p: p.cpu, reverse=True)
    background = [p for p in processes if p.cpu < 12 and p.memory < 12]
    memory_hogs = [p for p in processes if p.memory >= 28]

    for index, proc in enumerate(heavy):
        core = perf_cores[index % len(perf_cores)]
        actions.append(Action(
            type="CPU_AFFINITY",
            target=f"{proc.name}:{proc.pid}",
            command=f"taskset -pc {core} {proc.pid}",
            reason=f"High CPU process moved to performance core {core}.",
        ))
        actions.append(Action(
            type="PRIORITY_BOOST",
            target=f"{proc.name}:{proc.pid}",
            command=f"renice -n -5 -p {proc.pid}",
            reason="Latency-sensitive workload receives temporary priority boost.",
            risk="medium",
        ))

    for index, proc in enumerate(background[:8]):
        core = eff_cores[index % len(eff_cores)]
        actions.append(Action(
            type="BACKGROUND_PACKING",
            target=f"{proc.name}:{proc.pid}",
            command=f"taskset -pc {core} {proc.pid}",
            reason=f"Background task packed onto efficiency core {core}.",
        ))

    for proc in memory_hogs:
        actions.append(Action(
            type="MEMORY_PRESSURE",
            target=f"{proc.name}:{proc.pid}",
            command=f"echo advise-cold-pages pid={proc.pid}",
            reason="Candidate for cache trimming or inactive-page compression.",
        ))

    actions.append(Action(
        type="QUEUE_POLICY",
        target="system",
        command="simulate multi-level queue rebalance",
        reason="Foreground, inference, and background queues separated to reduce context switching.",
    ))
    return actions


def apply_actions(actions: List[Action]) -> None:
    for action in actions:
        if action.command.startswith("taskset") or action.command.startswith("renice"):
            subprocess.run(action.command.split(), check=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    actions = plan(load_processes(args.metrics))
    if args.apply:
        apply_actions(actions)
    print(json.dumps({"mode": "apply" if args.apply else "dry-run", "actions": [asdict(a) for a in actions]}, indent=2))


if __name__ == "__main__":
    main()
