from __future__ import annotations

from typing import Any


PROTECTED_PROCESS_NAMES = {
    "system idle process",
    "system",
    "registry",
    "secure system",
    "memory compression",
    "explorer.exe",
    "wininit.exe",
    "csrss.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "dwm.exe",
    "fontdrvhost.exe",
    "smss.exe",
    "winlogon.exe",
    "spoolsv.exe",
    "searchindexer.exe",
    "msmpeng.exe",
    "antimalware service executable",
    "init",
    "systemd",
    "kthreadd",
    "ksoftirqd",
    "rcu_sched",
    "migration",
    "watchdog",
    "dbus-daemon",
    "polkitd",
    "journald",
}

PROTECTED_PREFIXES = (
    "system idle",
    "system interrupts",
    "kworker/",
    "ksoftirqd/",
    "migration/",
    "rcu_",
    "watchdog/",
)


def normalized_process_name(proc: dict[str, Any]) -> str:
    return str(proc.get("name") or "").strip().lower()


def is_protected_process(proc: dict[str, Any]) -> bool:
    pid = int(proc.get("pid") or 0)
    name = normalized_process_name(proc)
    if pid <= 1:
        return True
    if name in PROTECTED_PROCESS_NAMES:
        return True
    return any(name.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def user_processes(processes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [proc for proc in processes if not is_protected_process(proc)]
