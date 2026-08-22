#!/usr/bin/env python3
"""Real distributed edge execution orchestrator for AstraOS.

Nodes are supplied as name=host:port entries. Each node should expose a TCP
health endpoint or accept a TCP connection for heartbeat measurement.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from dataclasses import dataclass, asdict


@dataclass
class EdgeNode:
    name: str
    host: str
    port: int


async def heartbeat(node: EdgeNode) -> dict:
    started = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(node.host, node.port), timeout=1.5)
        writer.close()
        await writer.wait_closed()
        latency = (time.perf_counter() - started) * 1000
        return {**asdict(node), "online": True, "latency_ms": round(latency, 2)}
    except Exception as exc:
        return {**asdict(node), "online": False, "latency_ms": None, "error": str(exc)}


def parse_nodes(raw: str) -> list[EdgeNode]:
    nodes = []
    for entry in [part.strip() for part in raw.split(",") if part.strip()]:
        name, _, target = entry.partition("=")
        host, _, port = target.partition(":")
        if not name or not host or not port:
            raise ValueError(f"Invalid node entry: {entry}. Expected name=host:port")
        nodes.append(EdgeNode(name=name, host=host, port=int(port)))
    return nodes


def allocate(results: list[dict]) -> dict[str, float]:
    online = [node for node in results if node["online"]]
    if not online:
        return {}
    scores = {}
    for node in online:
        latency = max(1.0, float(node["latency_ms"] or 1000))
        scores[node["name"]] = 1.0 / latency
    total = sum(scores.values())
    return {name: round(score / total * 100, 2) for name, score in scores.items()}


async def run(raw_nodes: str) -> dict:
    nodes = parse_nodes(raw_nodes)
    results = await asyncio.gather(*(heartbeat(node) for node in nodes))
    return {
        "timestamp": time.time(),
        "nodes": results,
        "allocation": allocate(results),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", required=True, help="Comma-separated real nodes: laptop=10.0.0.2:9100,jetson=10.0.0.3:9100")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run(args.nodes)), indent=2))


if __name__ == "__main__":
    main()
