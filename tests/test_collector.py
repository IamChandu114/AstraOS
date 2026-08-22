from backend.astraos.collector import TelemetryCollector


def test_collector_initialization():
    collector = TelemetryCollector()
    assert collector.previous_disk is not None
    assert collector.previous_net is not None
    assert collector.previous_time > 0


def test_collector_collect():
    collector = TelemetryCollector()
    snapshot = collector.collect()
    
    assert "timestamp" in snapshot
    assert "host" in snapshot
    assert "cpu" in snapshot
    assert "memory" in snapshot
    assert "swap" in snapshot
    assert "processes" in snapshot
    assert "disk" in snapshot
    assert "network" in snapshot
    assert "thermal" in snapshot
    assert "gpu" in snapshot
    assert "battery" in snapshot
    assert "kernel" in snapshot


def test_collector_host_info():
    collector = TelemetryCollector()
    snapshot = collector.collect()
    host = snapshot["host"]
    
    assert "hostname" in host
    assert "platform" in host
    assert "system" in host
    assert "python" in host
    assert "boot_time" in host


def test_collector_cpu_info():
    collector = TelemetryCollector()
    snapshot = collector.collect()
    cpu = snapshot["cpu"]
    
    assert "usage_percent" in cpu
    assert "per_core_percent" in cpu
    assert "logical_cores" in cpu
    assert "physical_cores" in cpu
    assert 0 <= cpu["usage_percent"] <= 100


def test_collector_memory_info():
    collector = TelemetryCollector()
    snapshot = collector.collect()
    memory = snapshot["memory"]
    
    assert "total_bytes" in memory
    assert "used_bytes" in memory
    assert "percent" in memory
    assert 0 <= memory["percent"] <= 100


def test_collector_processes_info():
    collector = TelemetryCollector()
    snapshot = collector.collect()
    processes = snapshot["processes"]
    
    assert "total" in processes
    assert "states" in processes
    assert "top" in processes
    assert processes["total"] > 0
    assert len(processes["top"]) <= 20


def test_collector_thermal_info():
    collector = TelemetryCollector()
    snapshot = collector.collect()
    thermal = snapshot["thermal"]
    
    assert "sensors" in thermal
    assert isinstance(thermal["sensors"], list)


def test_collector_gpu_info():
    collector = TelemetryCollector()
    snapshot = collector.collect()
    gpu = snapshot["gpu"]
    
    assert "available" in gpu
    assert "devices" in gpu
    assert isinstance(gpu["devices"], list)


def test_collector_battery_info():
    collector = TelemetryCollector()
    snapshot = collector.collect()
    battery = snapshot["battery"]
    
    assert "available" in battery
