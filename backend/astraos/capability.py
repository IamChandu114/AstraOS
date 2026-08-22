from __future__ import annotations

from typing import Any


def capability_state(name: str, active: bool, reason: str, remediation: str | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "active": active,
        "state": "active" if active else "inactive",
        "message": f"{name} active" if active else reason,
        "remediation": remediation,
    }


def host_capabilities(snapshot: dict[str, Any] | None, kernel: dict[str, Any], containers: dict[str, Any]) -> list[dict[str, Any]]:
    thermal_active = bool((snapshot or {}).get("thermal", {}).get("sensors"))
    gpu_active = bool((snapshot or {}).get("gpu", {}).get("available"))
    battery_active = bool((snapshot or {}).get("battery", {}).get("available"))
    return [
        capability_state(
            "Thermal Sensors",
            thermal_active,
            "Thermal sensors are not exposed by this host OS or hardware profile.",
            "Run on Linux with lm-sensors/sysfs thermal zones for physical thermal telemetry.",
        ),
        capability_state(
            "GPU Telemetry",
            gpu_active,
            "GPU telemetry adapter is inactive on current hardware.",
            "Install NVIDIA drivers and nvidia-smi, or run on a Jetson/NVIDIA host.",
        ),
        capability_state(
            "eBPF Runtime Adapter",
            bool(kernel.get("available")),
            "Kernel observability requires Linux perf/bpftrace tooling.",
            "Run AstraOS on Linux with perf or bpftrace installed and appropriate permissions.",
        ),
        capability_state(
            "Battery Telemetry",
            battery_active,
            "Battery telemetry is not reported by this host power subsystem.",
            "Run on a laptop host with OS battery sensor support.",
        ),
        capability_state(
            "Container Runtime",
            bool(containers.get("docker", {}).get("containers") or containers.get("kubernetes", {}).get("pods")),
            "Container observability is ready, but no active Docker/Kubernetes workloads are reporting.",
            "Start Docker Compose or configure kubectl context to populate container topology.",
        ),
    ]
