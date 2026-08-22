from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from typing import Any


class KernelObservability:
    """eBPF/perf adapter. Runs real tooling only when available on Linux."""

    def status(self) -> dict[str, Any]:
        available = platform.system() == "Linux" and (shutil.which("bpftrace") or shutil.which("perf"))
        return {
            "timestamp": time.time(),
            "platform": platform.system(),
            "available": bool(available),
            "adapter_state": "active" if available else "adapter_inactive",
            "bpftrace": shutil.which("bpftrace"),
            "perf": shutil.which("perf"),
            "requires_root": True,
            "message": "Kernel observability adapter active." if available else "Kernel observability requires Linux perf or bpftrace tooling on this host.",
        }

    def sample(self, seconds: int = 3) -> dict[str, Any]:
        seconds = max(1, min(seconds, 15))
        status = self.status()
        if platform.system() != "Linux":
            return {**status, "status": "adapter_inactive", "message": "eBPF tracing requires a Linux host; current host exposes fallback runtime counters only."}
        if shutil.which("bpftrace"):
            return self._bpftrace(seconds)
        if shutil.which("perf"):
            return self._perf_stat(seconds)
        return {**status, "status": "adapter_inactive", "message": "Install bpftrace or perf to enable kernel observability."}

    def _bpftrace(self, seconds: int) -> dict[str, Any]:
        program = (
            "tracepoint:sched:sched_switch { @ctx = count(); } "
            "tracepoint:raw_syscalls:sys_enter { @syscalls[comm] = count(); } "
            f"interval:s:{seconds} {{ exit(); }}"
        )
        try:
            output = subprocess.check_output(["bpftrace", "-e", program], text=True, stderr=subprocess.STDOUT, timeout=seconds + 5)
            return {"timestamp": time.time(), "status": "live", "tool": "bpftrace", "output": output}
        except subprocess.CalledProcessError as exc:
            return {"timestamp": time.time(), "status": "error", "tool": "bpftrace", "error": exc.output}
        except Exception as exc:
            return {"timestamp": time.time(), "status": "error", "tool": "bpftrace", "error": str(exc)}

    def _perf_stat(self, seconds: int) -> dict[str, Any]:
        try:
            output = subprocess.check_output(
                ["perf", "stat", "-e", "context-switches,cpu-migrations,page-faults,cycles,instructions", "sleep", str(seconds)],
                text=True,
                stderr=subprocess.STDOUT,
                timeout=seconds + 5,
            )
            return {"timestamp": time.time(), "status": "live", "tool": "perf", "output": output}
        except Exception as exc:
            return {"timestamp": time.time(), "status": "error", "tool": "perf", "error": str(exc)}

    def syscall_heatmap(self, trace_output: str) -> list[dict[str, Any]]:
        heatmap = []
        for line in trace_output.splitlines():
            if "@" not in line or ":" not in line:
                continue
            name, _, value = line.partition(":")
            try:
                count = int(value.strip())
            except ValueError:
                continue
            heatmap.append({"event": name.strip(), "count": count})
        return sorted(heatmap, key=lambda item: item["count"], reverse=True)[:32]
