from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any
from urllib.request import urlopen


class NodeRegistry:
    """Track real configured edge nodes through heartbeat probes."""

    def configured_nodes(self) -> list[dict[str, Any]]:
        raw = os.getenv("ASTRAOS_EDGE_NODES", "")
        nodes = []
        for entry in [part.strip() for part in raw.split(",") if part.strip()]:
            name, _, target = entry.partition("=")
            host, _, port = target.partition(":")
            if name and host and port:
                nodes.append({"name": name, "host": host, "port": int(port)})
        return nodes

    async def heartbeat(self) -> dict[str, Any]:
        nodes = self.configured_nodes()
        results = []
        for node in nodes:
            started = time.perf_counter()
            try:
                telemetry = await asyncio.wait_for(asyncio.to_thread(self._fetch_node_telemetry, node), timeout=1.5)
                latency = (time.perf_counter() - started) * 1000
                results.append({**node, "online": True, "latency_ms": round(latency, 2), "telemetry": telemetry})
            except Exception as exc:
                try:
                    reader, writer = await asyncio.wait_for(asyncio.open_connection(node["host"], node["port"]), timeout=1.5)
                    writer.close()
                    await writer.wait_closed()
                    latency = (time.perf_counter() - started) * 1000
                    results.append({**node, "online": True, "latency_ms": round(latency, 2), "telemetry": None, "message": "TCP heartbeat active; HTTP telemetry endpoint did not respond."})
                except Exception:
                    results.append({**node, "online": False, "latency_ms": None, "error": str(exc)})
        return {
            "timestamp": time.time(),
            "configured": len(nodes),
            "nodes": results,
            "message": "No real edge nodes configured. Set ASTRAOS_EDGE_NODES=name=host:port,... to enable discovery." if not nodes else "real heartbeat complete",
        }

    def _fetch_node_telemetry(self, node: dict[str, Any]) -> dict[str, Any]:
        with urlopen(f"http://{node['host']}:{node['port']}/telemetry", timeout=1.2) as response:
            return json.loads(response.read().decode("utf-8"))
