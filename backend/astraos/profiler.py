from __future__ import annotations

import platform
import shutil
import subprocess
import time
from typing import Any


class Profiler:
    """Real profiling adapter for perf/eBPF-capable Linux hosts."""

    def status(self) -> dict[str, Any]:
        return {
            "timestamp": time.time(),
            "platform": platform.system(),
            "perf": shutil.which("perf"),
            "bpftrace": shutil.which("bpftrace"),
            "available": platform.system() == "Linux" and bool(shutil.which("perf") or shutil.which("bpftrace")),
        }

    def profile(self, seconds: int = 5) -> dict[str, Any]:
        seconds = max(1, min(seconds, 30))
        status = self.status()
        if platform.system() != "Linux":
            return {**status, "status": "unsupported", "message": "perf/flamegraph profiling requires Linux."}
        if not shutil.which("perf"):
            return {**status, "status": "unavailable", "message": "Install perf to capture CPU profiles."}
        try:
            output = subprocess.check_output(
                ["perf", "stat", "-a", "--", "sleep", str(seconds)],
                text=True,
                stderr=subprocess.STDOUT,
                timeout=seconds + 5,
            )
            return {"timestamp": time.time(), "status": "live", "tool": "perf stat", "output": output}
        except Exception as exc:
            return {"timestamp": time.time(), "status": "error", "tool": "perf stat", "error": str(exc)}
