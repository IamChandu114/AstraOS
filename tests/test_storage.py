from backend.astraos.storage import TelemetryStore
import tempfile
import os


def test_storage_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = TelemetryStore(db_path)
        assert store.path.exists()


def test_storage_write_telemetry():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = TelemetryStore(db_path)
        
        payload = {
            "timestamp": 1.0,
            "cpu": {"usage_percent": 50.0},
            "memory": {"percent": 60.0},
        }
        store.write_telemetry(payload)
        
        latest = store.latest("telemetry")
        assert latest is not None
        assert latest["cpu"]["usage_percent"] == 50.0


def test_storage_write_prediction():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = TelemetryStore(db_path)
        
        payload = {
            "timestamp": 1.0,
            "cpu_spike": {"risk": "normal"},
            "workload_class": "balanced",
        }
        store.write_prediction(payload)
        
        latest = store.latest("predictions")
        assert latest is not None
        assert latest["workload_class"] == "balanced"


def test_storage_write_action():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = TelemetryStore(db_path)
        
        payload = {"test": "data"}
        store.write_action("test_action", payload)
        
        history = store.history("optimization_logs", 10)
        assert len(history) > 0
        # The history returns the payload directly, not wrapped in an action field
        assert history[0] == payload


def test_storage_write_benchmark():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = TelemetryStore(db_path)
        
        payload = {
            "timestamp": 1.0,
            "status": "real_benchmark",
            "metrics": [],
        }
        store.write_benchmark(payload)
        
        latest = store.latest("benchmarks")
        assert latest is not None
        assert latest["status"] == "real_benchmark"


def test_storage_latest():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = TelemetryStore(db_path)
        
        # No data yet
        latest = store.latest("telemetry")
        assert latest is None
        
        # Add data
        store.write_telemetry({"timestamp": 1.0, "cpu": {"usage_percent": 50.0}})
        latest = store.latest("telemetry")
        assert latest is not None


def test_storage_history():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = TelemetryStore(db_path)
        
        # Add multiple entries
        for i in range(5):
            store.write_telemetry({"timestamp": float(i), "cpu": {"usage_percent": 50.0 + i}})
        
        history = store.history("telemetry", 10)
        assert len(history) == 5
        assert history[0]["timestamp"] == 0.0
        assert history[-1]["timestamp"] == 4.0


def test_storage_history_limit():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        store = TelemetryStore(db_path)
        
        # Add more entries than limit
        for i in range(10):
            store.write_telemetry({"timestamp": float(i), "cpu": {"usage_percent": 50.0}})
        
        history = store.history("telemetry", 5)
        assert len(history) == 5
