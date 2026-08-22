from __future__ import annotations

import os
import socket
import time
from typing import Any

import psutil
from fastapi import FastAPI

STARTED_AT = time.time()
NODE_NAME = os.getenv("ASTRAOS_NODE_NAME", socket.gethostname())
NODE_ROLE = os.getenv("ASTRAOS_NODE_ROLE", "edge-worker")
NODE_WORKLOAD = os.getenv("ASTRAOS_NODE_WORKLOAD", "container telemetry")

app = FastAPI(title=f"AstraOS Node Agent {NODE_NAME}", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "node": NODE_NAME, "uptime_seconds": int(time.time() - STARTED_AT)}


@app.get("/telemetry")
async def telemetry() -> dict[str, Any]:
    cpu = psutil.cpu_percent(interval=0.05)
    mem = psutil.virtual_memory()
    net = psutil.net_io_counters()
    disk = psutil.disk_io_counters()
    return {
        "timestamp": time.time(),
        "name": NODE_NAME,
        "role": NODE_ROLE,
        "workload": NODE_WORKLOAD,
        "hostname": socket.gethostname(),
        "uptime_seconds": int(time.time() - STARTED_AT),
        "cpu_percent": round(cpu, 2),
        "memory_percent": round(mem.percent, 2),
        "memory_used_bytes": mem.used,
        "network": {
            "bytes_sent": getattr(net, "bytes_sent", None),
            "bytes_recv": getattr(net, "bytes_recv", None),
            "packets_sent": getattr(net, "packets_sent", None),
            "packets_recv": getattr(net, "packets_recv", None),
        },
        "disk": {
            "read_bytes": getattr(disk, "read_bytes", None),
            "write_bytes": getattr(disk, "write_bytes", None),
        },
        "telemetry_source": "real psutil metrics from node container",
    }
