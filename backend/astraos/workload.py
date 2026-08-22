from __future__ import annotations

from typing import Any

from backend.astraos.process_filters import is_protected_process


class WorkloadClassifier:
    """Classify real host workload patterns from process names and telemetry."""

    KEYWORDS = {
        "gaming": {"steam", "game", "unreal", "unity", "valorant", "fortnite", "minecraft"},
        "ai_inference": {"python", "torch", "tensorflow", "onnx", "triton", "cuda", "nvidia"},
        "rendering": {"blender", "maya", "houdini", "ffmpeg", "premiere", "resolve"},
        "browser_heavy": {"chrome", "msedge", "firefox", "brave", "browser"},
        "compiler_heavy": {"gcc", "g++", "clang", "rustc", "cargo", "javac", "msbuild", "ninja"},
        "background_compute": {"onedrive", "backup", "sync", "index", "search", "antimalware"},
        "containerized_services": {"docker", "containerd", "kubectl", "kubelet", "podman"},
        "distributed_workloads": {"ray", "dask", "spark", "mpi", "redis-server", "grpc"},
    }

    def classify(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        top = snapshot.get("processes", {}).get("top", [])
        scores = {name: 0.0 for name in self.KEYWORDS}
        evidence: dict[str, list[str]] = {name: [] for name in self.KEYWORDS}

        for proc in top:
            if is_protected_process(proc):
                continue
            proc_name = str(proc.get("name") or "").lower()
            weight = 1.0 + float(proc.get("cpu_percent") or 0) / 100 + float(proc.get("memory_percent") or 0)
            for category, keywords in self.KEYWORDS.items():
                if any(keyword in proc_name for keyword in keywords):
                    scores[category] += weight
                    evidence[category].append(f"{proc.get('name')} pid={proc.get('pid')}")

        cpu = float(snapshot.get("cpu", {}).get("usage_percent") or 0)
        memory = float(snapshot.get("memory", {}).get("percent") or 0)
        gpu_devices = snapshot.get("gpu", {}).get("devices", [])
        gpu_util = max([float(device.get("utilization_percent") or 0) for device in gpu_devices], default=0.0)
        net_kbps = float(snapshot.get("network", {}).get("bytes_recv_per_sec") or 0) / 1024

        if cpu > 75 and memory > 70:
            scores["compiler_heavy"] += 0.4
        if gpu_util > 55:
            scores["gaming"] += 0.5
            scores["ai_inference"] += 0.5
        if net_kbps > 3000:
            scores["distributed_workloads"] += 0.4

        category = max(scores, key=scores.get)
        confidence = min(0.96, scores[category] / max(1.0, sum(scores.values()) or 1.0) + 0.24)
        if scores[category] == 0:
            category = "balanced"
            confidence = 0.35

        return {
            "category": category,
            "confidence": round(confidence, 3),
            "scores": {key: round(value, 3) for key, value in scores.items()},
            "evidence": {key: value[:5] for key, value in evidence.items() if value},
            "policy_profile": self.policy_for(category),
        }

    def policy_for(self, category: str) -> dict[str, Any]:
        profiles = {
            "gaming": {"priority": "foreground_latency", "gpu": "prefer", "background": "throttle"},
            "ai_inference": {"priority": "tensor_throughput", "gpu": "stabilize", "thermal": "proactive"},
            "rendering": {"priority": "sustained_throughput", "thermal": "avoid_spikes"},
            "browser_heavy": {"priority": "interactive_latency", "memory": "tab_pressure"},
            "compiler_heavy": {"priority": "parallel_build_balance", "cpu": "spread"},
            "background_compute": {"priority": "low_impact", "cpu": "efficiency_cores"},
            "containerized_services": {"priority": "cgroup_balance", "memory": "limit_detection"},
            "distributed_workloads": {"priority": "network_latency", "edge": "balance"},
            "balanced": {"priority": "observe"},
        }
        return profiles.get(category, profiles["balanced"])
