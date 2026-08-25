from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psutil


def _safe_call(default: Any, fn):
    try:
        return fn()
    except Exception:
        return default


def _safe_io_call(default: Any, fn):
    """Like _safe_call but logs EOVERFLOW (Errno 75) without crashing the whole collect()."""
    try:
        return fn()
    except OSError as exc:
        # Errno 75 = EOVERFLOW: kernel IO counter overflowed (common on 32-bit /proc counters)
        # Return default and let caller reset previous reference for clean delta on next tick
        if exc.errno == 75:
            return default
        raise
    except Exception:
        return default


def _round(value: float | int | None, digits: int = 2) -> float | None:
    if value is None:
        return None
    return round(float(value), digits)


@dataclass
class TelemetryCollector:
    """Collect real host telemetry using psutil, Linux procfs/sysfs, and vendor tools."""

    previous_disk: Any = None
    previous_net: Any = None
    previous_time: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        _safe_call(None, lambda: psutil.cpu_percent(interval=None, percpu=True))
        self.previous_disk = _safe_io_call(None, psutil.disk_io_counters)
        self.previous_net = _safe_io_call(None, psutil.net_io_counters)
        self.previous_time = time.time()

    def collect(self) -> dict[str, Any]:
        now = time.time()
        elapsed = max(0.001, now - self.previous_time)
        disk = _safe_io_call(None, psutil.disk_io_counters)
        net = _safe_io_call(None, psutil.net_io_counters)
        # Reset previous references if IO counters failed (overflow recovery)
        if disk is None:
            self.previous_disk = None
        if net is None:
            self.previous_net = None

        snapshot = {
            "timestamp": now,
            "host": _safe_call({}, self._host),
            "cpu": _safe_call({}, self._cpu),
            "memory": _safe_call({}, self._memory),
            "swap": _safe_call({}, self._swap),
            "processes": _safe_call({"total": 0, "states": {}, "top": []}, self._processes),
            "disk": _safe_io_call({"root_percent": None, "read_bytes_per_sec": None, "write_bytes_per_sec": None}, lambda: self._disk(disk, elapsed)),
            "network": _safe_io_call({"bytes_sent_per_sec": None, "bytes_recv_per_sec": None}, lambda: self._network(net, elapsed)),
            "thermal": _safe_call({"sensors": [], "hottest_c": None}, self._thermal),
            "gpu": _safe_call({"available": False, "devices": []}, self._gpu),
            "battery": _safe_call({"available": False}, self._battery),
            "kernel": _safe_call({"procfs_available": False}, self._kernel),
        }

        self.previous_disk = disk
        self.previous_net = net
        self.previous_time = now
        return snapshot

    def _host(self) -> dict[str, Any]:
        return {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
            "boot_time": _safe_call(None, psutil.boot_time),
        }

    def _cpu(self) -> dict[str, Any]:
        freq = _safe_call(None, psutil.cpu_freq)
        stats = _safe_call(None, psutil.cpu_stats)
        load_avg = _safe_call((None, None, None), os.getloadavg) if hasattr(os, "getloadavg") else (None, None, None)
        per_core = _safe_call([], lambda: psutil.cpu_percent(interval=None, percpu=True))
        return {
            "usage_percent": _round(sum(per_core) / max(1, len(per_core))) if per_core else None,
            "per_core_percent": [_round(v) for v in per_core],
            "logical_cores": _safe_call(None, lambda: psutil.cpu_count(logical=True)),
            "physical_cores": _safe_call(None, lambda: psutil.cpu_count(logical=False)),
            "frequency_mhz": {
                "current": _round(getattr(freq, "current", None)),
                "min": _round(getattr(freq, "min", None)),
                "max": _round(getattr(freq, "max", None)),
            },
            "load_average": [_round(v) for v in load_avg],
            "context_switches": getattr(stats, "ctx_switches", None),
            "interrupts": getattr(stats, "interrupts", None),
        }

    def _memory(self) -> dict[str, Any]:
        mem = _safe_call(None, psutil.virtual_memory)
        if not mem:
            return {}
        return {
            "total_bytes": mem.total,
            "available_bytes": mem.available,
            "used_bytes": mem.used,
            "free_bytes": mem.free,
            "percent": _round(mem.percent),
            "active_bytes": getattr(mem, "active", None),
            "inactive_bytes": getattr(mem, "inactive", None),
            "buffers_bytes": getattr(mem, "buffers", None),
            "cached_bytes": getattr(mem, "cached", None),
            "fragmentation": self._memory_fragmentation(mem),
        }

    def _swap(self) -> dict[str, Any]:
        swap = _safe_call(None, psutil.swap_memory)
        if not swap:
            return {}
        return {
            "total_bytes": swap.total,
            "used_bytes": swap.used,
            "free_bytes": swap.free,
            "percent": _round(swap.percent),
            "sin": swap.sin,
            "sout": swap.sout,
        }

    def _processes(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        states: dict[str, int] = {}
        for proc in psutil.process_iter(["pid", "name", "username", "status", "num_threads", "cpu_percent", "memory_percent", "nice"]):
            try:
                info = proc.info
                status = str(info.get("status") or "unknown")
                states[status] = states.get(status, 0) + 1
                items.append({
                    "pid": info.get("pid"),
                    "name": info.get("name") or "unknown",
                    "username": info.get("username"),
                    "status": status,
                    "threads": info.get("num_threads"),
                    "cpu_percent": _round(info.get("cpu_percent") or 0.0),
                    "memory_percent": _round(info.get("memory_percent") or 0.0, 3),
                    "nice": info.get("nice"),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                continue

        items.sort(key=lambda item: (item["cpu_percent"], item["memory_percent"]), reverse=True)
        return {
            "total": len(items),
            "states": states,
            "top": items[:20],
        }

    def _disk(self, current, elapsed: float) -> dict[str, Any]:
        usage = _safe_call(None, lambda: psutil.disk_usage("/"))
        previous = self.previous_disk
        read_bps = write_bps = None
        if current and previous:
            read_bps = max(0, current.read_bytes - previous.read_bytes) / elapsed
            write_bps = max(0, current.write_bytes - previous.write_bytes) / elapsed
        return {
            "root_percent": _round(getattr(usage, "percent", None)),
            "read_bytes_per_sec": _round(read_bps),
            "write_bytes_per_sec": _round(write_bps),
            "read_count": getattr(current, "read_count", None),
            "write_count": getattr(current, "write_count", None),
        }

    def _network(self, current, elapsed: float) -> dict[str, Any]:
        previous = self.previous_net
        sent_bps = recv_bps = None
        if current and previous:
            sent_bps = max(0, current.bytes_sent - previous.bytes_sent) / elapsed
            recv_bps = max(0, current.bytes_recv - previous.bytes_recv) / elapsed
        return {
            "bytes_sent_per_sec": _round(sent_bps),
            "bytes_recv_per_sec": _round(recv_bps),
            "packets_sent": getattr(current, "packets_sent", None),
            "packets_recv": getattr(current, "packets_recv", None),
        }

    def _thermal(self) -> dict[str, Any]:
        sensors = []
        psutil_temps = _safe_call({}, psutil.sensors_temperatures) if hasattr(psutil, "sensors_temperatures") else {}
        for chip, entries in psutil_temps.items():
            for entry in entries:
                sensors.append({
                    "source": chip,
                    "label": entry.label or chip,
                    "current_c": _round(entry.current),
                    "high_c": _round(entry.high),
                    "critical_c": _round(entry.critical),
                })

        thermal_root = Path("/sys/class/thermal")
        if thermal_root.exists():
            for zone in thermal_root.glob("thermal_zone*"):
                temp_path = zone / "temp"
                if not temp_path.exists():
                    continue
                raw = _safe_call(None, lambda p=temp_path: float(p.read_text().strip()))
                if raw is None:
                    continue
                label = _safe_call(zone.name, lambda z=zone: (z / "type").read_text().strip())
                sensors.append({
                    "source": zone.name,
                    "label": label,
                    "current_c": _round(raw / 1000 if raw > 1000 else raw),
                    "high_c": None,
                    "critical_c": None,
                })

        hottest = max([s["current_c"] for s in sensors if s["current_c"] is not None and s["current_c"] > -100], default=None)
        return {
            "sensors": [s for s in sensors if s["current_c"] is not None and s["current_c"] > -100],
            "hottest_c": hottest,
        }

    def _gpu(self) -> dict[str, Any]:
        if not shutil.which("nvidia-smi"):
            return {"available": False, "devices": []}
        query = "index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw"
        cmd = [
            "nvidia-smi",
            f"--query-gpu={query}",
            "--format=csv,noheader,nounits",
        ]
        try:
            output = subprocess.check_output(cmd, text=True, timeout=1.5)
        except Exception:
            return {"available": False, "devices": []}

        devices = []
        for line in output.strip().splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) != 7:
                continue
            devices.append({
                "index": int(parts[0]),
                "name": parts[1],
                "utilization_percent": _round(_float_or_none(parts[2])),
                "memory_used_mib": _round(_float_or_none(parts[3])),
                "memory_total_mib": _round(_float_or_none(parts[4])),
                "temperature_c": _round(_float_or_none(parts[5])),
                "power_watts": _round(_float_or_none(parts[6])),
            })
        return {"available": bool(devices), "devices": devices}

    def _battery(self) -> dict[str, Any]:
        battery = _safe_call(None, psutil.sensors_battery) if hasattr(psutil, "sensors_battery") else None
        if battery is None:
            return {"available": False}
        return {
            "available": True,
            "percent": _round(battery.percent),
            "power_plugged": battery.power_plugged,
            "seconds_left": battery.secsleft,
        }

    def _kernel(self) -> dict[str, Any]:
        stat_path = Path("/proc/stat")
        if not stat_path.exists():
            return {"procfs_available": False}
        ctxt = processes = None
        for line in stat_path.read_text(errors="ignore").splitlines():
            if line.startswith("ctxt "):
                ctxt = int(line.split()[1])
            elif line.startswith("processes "):
                processes = int(line.split()[1])
        return {
            "procfs_available": True,
            "context_switches_total": ctxt,
            "processes_forked_total": processes,
        }

    def _memory_fragmentation(self, mem) -> list[float]:
        values = [
            getattr(mem, "percent", 0.0),
            ((getattr(mem, "cached", 0) or 0) / mem.total) * 100 if mem.total else 0,
            ((getattr(mem, "inactive", 0) or 0) / mem.total) * 100 if mem.total else 0,
            ((getattr(mem, "active", 0) or 0) / mem.total) * 100 if mem.total else 0,
        ]
        top_memory = []
        for proc in psutil.process_iter(["memory_percent"]):
            try:
                top_memory.append(float(proc.info.get("memory_percent") or 0.0))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        top_memory.sort(reverse=True)
        values.extend(top_memory[:12])
        if not values:
            return []
        max_value = max(values) or 1.0
        return [_round(min(100.0, value / max_value * 100.0)) for value in values[:16]]


def _float_or_none(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None
