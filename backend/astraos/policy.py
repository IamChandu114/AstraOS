from __future__ import annotations

import os
import platform
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

import psutil

from backend.astraos.process_filters import is_protected_process


class OptimizationPolicy:
    """Plan and optionally apply safe, auditable optimization actions."""

    def plan(self, snapshot: dict[str, Any], prediction: dict[str, Any] | None = None) -> dict[str, Any]:
        actions = []
        protected = []
        cpu = float(snapshot.get("cpu", {}).get("usage_percent") or 0)
        memory = float(snapshot.get("memory", {}).get("percent") or 0)
        temp = snapshot.get("thermal", {}).get("hottest_c")
        top_processes = snapshot.get("processes", {}).get("top", [])

        if cpu > 75 or self._risk(prediction, "cpu_spike"):
            for proc in top_processes[:8]:
                pid = int(proc.get("pid") or 0)
                if is_protected_process(proc):
                    protected.append({"pid": pid, "process": proc.get("name"), "reason": "critical or system-owned process protected"})
                    continue
                if (proc.get("cpu_percent") or 0) > 10:
                    actions.append({
                        "type": "cpu_affinity",
                        "pid": proc["pid"],
                        "process": proc["name"],
                        "reason": "High CPU load detected from real telemetry.",
                        "apply_supported": hasattr(psutil.Process(), "cpu_affinity") if psutil.pid_exists(os.getpid()) else False,
                    })
                    actions.append({
                        "type": "renice",
                        "pid": proc["pid"],
                        "process": proc["name"],
                        "nice": 5,
                        "reason": "Lower priority for high-load background candidate.",
                        "apply_supported": True,
                    })
                    actions.append({
                        "type": "process_isolation",
                        "pid": proc["pid"],
                        "process": proc["name"],
                        "reason": "Isolate high-load process onto a deterministic CPU set.",
                        "apply_supported": psutil.pid_exists(pid),
                    })

        if platform.system() == "Linux" and (cpu > 85 or self._risk(prediction, "cpu_spike")):
            actions.append({
                "type": "cgroup_throttle",
                "group": "astraos-throttled",
                "cpu_max": "50000 100000",
                "reason": "Use cgroup v2 CPU quota for aggressive background pressure.",
                "apply_supported": Path("/sys/fs/cgroup").exists(),
                "requires_root": True,
            })

        if memory > 82 or self._risk(prediction, "memory_pressure"):
            actions.append({
                "type": "memory_pressure",
                "reason": "Memory pressure detected from real RAM telemetry.",
                "apply_supported": platform.system() == "Linux",
                "linux_commands": ["sync", "echo 1 > /proc/sys/vm/drop_caches"],
                "safe_default": "recommend_only",
            })

        if temp is not None and float(temp) > 82 or self._risk(prediction, "thermal"):
            actions.append({
                "type": "thermal_mitigation",
                "reason": "Thermal forecast or sensor reading exceeded threshold.",
                "apply_supported": False,
                "safe_default": "recommend_power_limit_or_workload_migration",
            })

        if not actions:
            actions.append({
                "type": "observe",
                "reason": "No optimization needed based on current real telemetry.",
                "apply_supported": False,
            })

        return {
            "timestamp": time.time(),
            "plan_id": f"plan-{uuid.uuid4().hex[:12]}",
            "mode": "plan",
            "actions": actions,
            "protected_processes": protected[:12],
            "policy": {
                "protected_mode": True,
                "rollback_supported": True,
                "apply_gate": "ASTRAOS_ENABLE_APPLY=1",
                "critical_process_protection": "enabled",
            },
            "requires_apply_enabled": True,
        }

    def apply(self, plan: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        execution_id = f"exec-{uuid.uuid4().hex[:12]}"
        if os.getenv("ASTRAOS_ENABLE_APPLY") != "1":
            return {
                "timestamp": time.time(),
                "execution_id": execution_id,
                "mode": "blocked",
                "message": "Set ASTRAOS_ENABLE_APPLY=1 to allow real host scheduling changes.",
                "protected_mode": True,
                "rollback_plan": [],
                "results": [],
            }

        results = []
        rollback_plan = []
        for action in plan.get("actions", []):
            result = {"action": action, "status": "skipped", "execution_id": execution_id}
            try:
                if action.get("pid") and not psutil.pid_exists(int(action["pid"])):
                    result["status"] = "process_exited"
                    results.append(result)
                    continue
                if action.get("pid"):
                    live_proc = psutil.Process(int(action["pid"]))
                    proc_view = {"pid": live_proc.pid, "name": live_proc.name(), "username": live_proc.username()}
                    if is_protected_process(proc_view):
                        result["status"] = "protected"
                        result["message"] = "Critical process protection blocked this action."
                        results.append(result)
                        continue
                if action["type"] == "renice" and action.get("pid"):
                    proc = psutil.Process(int(action["pid"]))
                    previous_nice = proc.nice()
                    proc.nice(int(action.get("nice", 5)))
                    rollback_plan.append({"type": "renice", "pid": proc.pid, "nice": previous_nice})
                    result["status"] = "applied"
                    result["rollback_available"] = True
                elif action["type"] == "cpu_affinity" and action.get("pid") and hasattr(psutil.Process(int(action["pid"])), "cpu_affinity"):
                    cores = list(range(psutil.cpu_count(logical=True) or 1))
                    if cores:
                        proc = psutil.Process(int(action["pid"]))
                        previous_affinity = proc.cpu_affinity()
                        proc.cpu_affinity([cores[int(action["pid"]) % len(cores)]])
                        rollback_plan.append({"type": "cpu_affinity", "pid": proc.pid, "cores": previous_affinity})
                        result["status"] = "applied"
                        result["core_set"] = proc.cpu_affinity()
                        result["rollback_available"] = True
                elif action["type"] == "process_isolation" and action.get("pid"):
                    proc = psutil.Process(int(action["pid"]))
                    if hasattr(proc, "cpu_affinity"):
                        cores = list(range(psutil.cpu_count(logical=True) or 1))
                        target = cores[-1:] if cores else []
                        if target:
                            previous_affinity = proc.cpu_affinity()
                            proc.cpu_affinity(target)
                            rollback_plan.append({"type": "cpu_affinity", "pid": proc.pid, "cores": previous_affinity})
                            result["status"] = "applied"
                            result["core_set"] = target
                            result["rollback_available"] = True
                elif action["type"] == "cgroup_throttle" and platform.system() == "Linux":
                    result.update(self._apply_cgroup_throttle(action))
                elif action["type"] == "memory_pressure" and platform.system() == "Linux":
                    subprocess.run(["sync"], check=False)
                    result["status"] = "recommendation_only"
                    result["message"] = "Cache drop is intentionally not executed automatically; requires operator confirmation."
                else:
                    result["status"] = "recommendation_only"
            except (psutil.AccessDenied, psutil.NoSuchProcess, PermissionError) as exc:
                result["status"] = "denied"
                result["error"] = str(exc)
            except Exception as exc:
                result["status"] = "error"
                result["error"] = str(exc)
            results.append(result)
        return {
            "timestamp": time.time(),
            "execution_id": execution_id,
            "mode": "apply",
            "protected_mode": True,
            "execution_duration_ms": round((time.perf_counter() - started) * 1000, 2),
            "rollback_plan": rollback_plan,
            "rollback_status": "available" if rollback_plan else "not_required",
            "results": results,
        }

    def rollback(self, rollback_plan: list[dict[str, Any]]) -> dict[str, Any]:
        results = []
        for action in rollback_plan:
            result = {"action": action, "status": "skipped"}
            try:
                if not psutil.pid_exists(int(action.get("pid") or 0)):
                    result["status"] = "process_exited"
                elif action.get("type") == "renice":
                    psutil.Process(int(action["pid"])).nice(int(action["nice"]))
                    result["status"] = "rolled_back"
                elif action.get("type") == "cpu_affinity":
                    proc = psutil.Process(int(action["pid"]))
                    if hasattr(proc, "cpu_affinity"):
                        proc.cpu_affinity(list(action.get("cores") or []))
                        result["status"] = "rolled_back"
            except Exception as exc:
                result["status"] = "error"
                result["error"] = str(exc)
            results.append(result)
        return {"timestamp": time.time(), "mode": "rollback", "results": results}

    def _risk(self, prediction: dict[str, Any] | None, key: str) -> bool:
        if not prediction:
            return False
        return prediction.get(key, {}).get("risk") in {"warning", "critical"}

    def _apply_cgroup_throttle(self, action: dict[str, Any]) -> dict[str, Any]:
        group = str(action.get("group") or "astraos-throttled")
        cgroup_root = Path("/sys/fs/cgroup")
        target = cgroup_root / group
        try:
            target.mkdir(exist_ok=True)
            (target / "cpu.max").write_text(str(action.get("cpu_max") or "50000 100000"))
            return {"status": "applied", "cgroup": str(target), "cpu_max": action.get("cpu_max")}
        except PermissionError as exc:
            return {"status": "denied", "error": str(exc), "cgroup": str(target)}
        except Exception as exc:
            return {"status": "error", "error": str(exc), "cgroup": str(target)}
