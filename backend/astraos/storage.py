from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any


class TelemetryStore:
    """Durable local store for telemetry, predictions, actions, and benchmarks."""

    def __init__(self, path: str | Path = "data/astraos.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp);

                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS optimization_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS node_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    node TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS incident_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS predictive_alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )

    def write_telemetry(self, payload: dict[str, Any]) -> None:
        self._insert("telemetry", payload.get("timestamp", time.time()), payload)

    def write_prediction(self, payload: dict[str, Any]) -> None:
        self._insert("predictions", payload.get("timestamp", time.time()), payload)

    def write_action(self, action: str, payload: dict[str, Any]) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO optimization_logs(timestamp, action, payload) VALUES (?, ?, ?)",
                (time.time(), action, json.dumps(payload)),
            )

    def write_benchmark(self, payload: dict[str, Any]) -> None:
        self._insert("benchmarks", payload.get("timestamp", time.time()), payload)

    def write_incident(self, payload: dict[str, Any]) -> None:
        self._insert("incident_history", payload.get("timestamp", time.time()), payload)

    def write_predictive_alerts(self, payload: dict[str, Any]) -> None:
        self._insert("predictive_alert_history", payload.get("timestamp", time.time()), payload)

    def latest(self, table: str) -> dict[str, Any] | None:
        with self.lock, self._connect() as conn:
            row = conn.execute(f"SELECT payload FROM {table} ORDER BY timestamp DESC LIMIT 1").fetchone()
        return json.loads(row[0]) if row else None

    def history(self, table: str, limit: int = 300) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 5000))
        with self.lock, self._connect() as conn:
            rows = conn.execute(f"SELECT payload FROM {table} ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(row[0]) for row in reversed(rows)]

    def _insert(self, table: str, timestamp: float, payload: dict[str, Any]) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                f"INSERT INTO {table}(timestamp, payload) VALUES (?, ?)",
                (timestamp, json.dumps(payload)),
            )
