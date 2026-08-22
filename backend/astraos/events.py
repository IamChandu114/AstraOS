from __future__ import annotations

import time
from collections import deque
from typing import Any


class EventStream:
    """Operational event buffer used by REST and WebSocket clients."""

    def __init__(self, maxlen: int = 500) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def emit(self, level: str, node: str, message: str, category: str = "runtime", **fields: Any) -> dict[str, Any]:
        event = {
            "timestamp": time.time(),
            "time": time.strftime("%H:%M:%S"),
            "level": level,
            "node": node,
            "category": category,
            "message": message,
            **fields,
        }
        self._events.append(event)
        return event

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._events)[-max(1, min(limit, 500)) :]

    def seed(self) -> None:
        if self._events:
            return
        self.emit("info", "astra-control-plane", "AstraOS runtime initialized.", "startup")
        self.emit("info", "astra-control-plane", "Telemetry collectors attached to host sensors.", "collector")
