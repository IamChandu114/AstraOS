from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from typing import Any


class ContainerAwareness:
    """Discover real Docker/Kubernetes workloads when tools are available."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] | None = None
        self._cache_at = 0.0

    def inspect(self) -> dict[str, Any]:
        ttl = float(os.getenv("ASTRAOS_CONTAINER_CACHE_SECONDS", "15"))
        now = time.time()
        if self._cache and now - self._cache_at < ttl:
            cached = dict(self._cache)
            cached["cached"] = True
            cached["cache_age_seconds"] = round(now - self._cache_at, 2)
            return cached
        docker = self._docker()
        kubernetes = self._kubernetes()
        payload = {
            "timestamp": now,
            "docker": docker,
            "kubernetes": kubernetes,
            "containerized": bool(docker.get("containers") or kubernetes.get("pods")),
            "cached": False,
        }
        self._cache = payload
        self._cache_at = now
        return payload

    def _docker(self) -> dict[str, Any]:
        if not shutil.which("docker"):
            return {"available": False, "containers": []}
        try:
            output = subprocess.check_output(
                ["docker", "stats", "--no-stream", "--format", "{{json .}}"],
                text=True,
                stderr=subprocess.STDOUT,
                timeout=float(os.getenv("ASTRAOS_DOCKER_TIMEOUT_SECONDS", "2")),
            )
            containers = []
            for line in output.splitlines():
                if line.strip():
                    containers.append(json.loads(line))
            return {"available": True, "containers": containers}
        except Exception as exc:
            return {"available": True, "error": str(exc), "containers": []}

    def _kubernetes(self) -> dict[str, Any]:
        if not shutil.which("kubectl"):
            return {"available": False, "pods": []}
        try:
            output = subprocess.check_output(
                ["kubectl", "get", "pods", "-A", "-o", "json"],
                text=True,
                stderr=subprocess.STDOUT,
                timeout=float(os.getenv("ASTRAOS_KUBECTL_TIMEOUT_SECONDS", "2")),
            )
            payload = json.loads(output)
            pods = [
                {
                    "namespace": item.get("metadata", {}).get("namespace"),
                    "name": item.get("metadata", {}).get("name"),
                    "phase": item.get("status", {}).get("phase"),
                    "node": item.get("spec", {}).get("nodeName"),
                }
                for item in payload.get("items", [])
            ]
            return {"available": True, "pods": pods}
        except Exception as exc:
            return {"available": True, "error": str(exc), "pods": []}
