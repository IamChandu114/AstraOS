from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class NodeProfile:
    name: str
    role: str
    workload: str
    cpu_base: float
    memory_base: float
    network_base: float
    phase: float


class DistributedFabric:
    """Deterministic local distributed infrastructure model for orchestration demos."""

    def __init__(self) -> None:
        self.started_at = time.time()
        self._stress: dict[str, dict[str, Any]] = {}
        self.profiles = [
            NodeProfile("astra-node-1", "edge-cpu-worker", "cpu-heavy inference batch", 78, 54, 8, 0.3),
            NodeProfile("astra-node-2", "memory-worker", "feature-cache pressure", 48, 83, 12, 1.7),
            NodeProfile("astra-node-3", "network-gateway", "stream aggregation", 42, 58, 76, 2.4),
            NodeProfile("astra-node-4", "standby-worker", "idle failover pool", 14, 31, 4, 3.2),
        ]

    def apply_stress(self, mode: str, intensity: float = 1.0, duration_seconds: int = 90) -> dict[str, Any]:
        intensity = max(0.1, min(float(intensity), 2.0))
        self._stress[mode] = {"until": time.time() + max(5, duration_seconds), "intensity": intensity}
        return {"mode": mode, "intensity": intensity, "expires_at": self._stress[mode]["until"]}

    def snapshot(self) -> dict[str, Any]:
        now = time.time()
        nodes = [self._node(profile, now) for profile in self.profiles]
        overloaded = [node for node in nodes if node["health_score"] < 72]
        target = max(nodes, key=lambda node: node["health_score"])
        events = []
        for node in overloaded:
            events.append({
                "timestamp": now,
                "time": time.strftime("%H:%M:%S", time.localtime(now)),
                "source": node["name"],
                "target": target["name"],
                "action": "workload_migration_recommendation",
                "reason": f"{node['dominant_pressure']} pressure exceeded orchestration threshold",
                "confidence": round(0.78 + (100 - node["health_score"]) / 300, 3),
            })
        total_cpu = sum(node["cpu_percent"] for node in nodes) / len(nodes)
        total_mem = sum(node["memory_percent"] for node in nodes) / len(nodes)
        return {
            "timestamp": now,
            "cluster": "astra-local-fabric",
            "mode": "clearly_labeled_container_node_simulation",
            "data_source": "AstraOS deterministic node model for local Docker/edge orchestration demos",
            "node_count": len(nodes),
            "online": len([node for node in nodes if node["status"] == "online"]),
            "health_score": round(sum(node["health_score"] for node in nodes) / len(nodes), 2),
            "aggregate": {
                "cpu_percent": round(total_cpu, 2),
                "memory_percent": round(total_mem, 2),
                "network_mbps": round(sum(node["network_mbps"] for node in nodes), 2),
            },
            "nodes": nodes,
            "orchestration_events": events,
            "active_stressors": self._active_stressors(now),
        }

    def _node(self, profile: NodeProfile, now: float) -> dict[str, Any]:
        wave = math.sin(now / 7 + profile.phase) * 7
        cpu = profile.cpu_base + wave
        memory = profile.memory_base + math.cos(now / 9 + profile.phase) * 5
        network = profile.network_base + abs(math.sin(now / 5 + profile.phase)) * 18
        for mode, stress in self._active_stressors(now).items():
            intensity = stress["intensity"]
            if mode == "cpu" and profile.name == "astra-node-1":
                cpu += 18 * intensity
            elif mode == "memory" and profile.name == "astra-node-2":
                memory += 12 * intensity
            elif mode == "network" and profile.name == "astra-node-3":
                network += 35 * intensity
            elif mode == "thermal" and profile.name in {"astra-node-1", "astra-node-2"}:
                cpu += 8 * intensity
            elif mode == "disk" and profile.name == "astra-node-2":
                memory += 6 * intensity
                network += 10 * intensity
            elif mode == "container_crash" and profile.name == "astra-node-3":
                cpu += 12 * intensity
                network = max(0, network - 30 * intensity)
            elif mode == "node_crash" and profile.name == "astra-node-4":
                cpu = 0
                memory = 0
                network = 0
        cpu = max(0, min(cpu, 99))
        memory = max(0, min(memory, 98))
        network = max(0, network)
        pressure = max(cpu, memory, min(network, 100))
        health = max(20, 100 - (pressure - 55) * 0.8 if pressure > 55 else 98 - pressure * 0.08)
        status = "online"
        if "node_crash" in self._active_stressors(now) and profile.name == "astra-node-4":
            status = "degraded"
            health = 28
        if "container_crash" in self._active_stressors(now) and profile.name == "astra-node-3":
            status = "container_restarting"
            health = min(health, 54)
        dominant = max({"cpu": cpu, "memory": memory, "network": min(network, 100)}, key={"cpu": cpu, "memory": memory, "network": min(network, 100)}.get)
        return {
            "name": profile.name,
            "role": profile.role,
            "workload": profile.workload,
            "status": status,
            "uptime_seconds": int(now - self.started_at),
            "heartbeat_age_ms": int(abs(math.sin(now + profile.phase)) * 42 + 8),
            "cpu_percent": round(cpu, 2),
            "memory_percent": round(memory, 2),
            "network_mbps": round(network, 2),
            "health_score": round(health, 2),
            "dominant_pressure": dominant,
            "tasks": max(1, int((cpu + memory) / 28)),
            "telemetry_source": "simulated container node" if status == "online" else "simulated chaos node state",
        }

    def _active_stressors(self, now: float) -> dict[str, dict[str, Any]]:
        expired = [key for key, stress in self._stress.items() if stress["until"] < now]
        for key in expired:
            self._stress.pop(key, None)
        return dict(self._stress)
