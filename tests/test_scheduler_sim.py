from backend.astraos.scheduler_sim import SchedulerSimulator


def sample_snapshot():
    return {
        "timestamp": 1.0,
        "cpu": {
            "usage_percent": 70.0,
            "logical_cores": 8,
            "physical_cores": 4,
        },
        "processes": {
            "total": 10,
            "top": [
                {"pid": 1001, "name": "python", "cpu_percent": 25.0, "memory_percent": 5.0, "nice": 0},
                {"pid": 1002, "name": "chrome", "cpu_percent": 20.0, "memory_percent": 8.0, "nice": 0},
                {"pid": 1003, "name": "node", "cpu_percent": 15.0, "memory_percent": 4.0, "nice": 0},
                {"pid": 1004, "name": "firefox", "cpu_percent": 10.0, "memory_percent": 6.0, "nice": 0},
            ],
        },
    }


def test_scheduler_simulator_comparison():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    result = sim.compare(snapshot)
    
    assert "timestamp" in result
    assert "cores" in result
    assert "process_count" in result
    assert "linux_cfs" in result
    assert "astra_scheduler" in result
    assert "improvement_estimate" in result


def test_scheduler_cfs_baseline():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    result = sim.compare(snapshot)
    
    cfs = result["linux_cfs"]
    assert "core_loads" in cfs
    assert "imbalance" in cfs
    assert "latency_score" in cfs
    assert "timeline" in cfs
    assert len(cfs["core_loads"]) == result["cores"]


def test_scheduler_astra():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    result = sim.compare(snapshot)
    
    astra = result["astra_scheduler"]
    assert "core_loads" in astra
    assert "imbalance" in astra
    assert "latency_score" in astra
    assert "timeline" in astra
    assert len(astra["core_loads"]) == result["cores"]


def test_scheduler_improvement_estimate():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    result = sim.compare(snapshot)
    
    improvement = result["improvement_estimate"]
    assert "core_balance_delta" in improvement
    assert "latency_score_delta" in improvement


def test_scheduler_load_balancing():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    result = sim.compare(snapshot)
    
    # Astra should have better balance (lower imbalance)
    cfs_imbalance = result["linux_cfs"]["imbalance"]
    astra_imbalance = result["astra_scheduler"]["imbalance"]
    
    # Astra should have equal or better balance
    assert astra_imbalance <= cfs_imbalance


def test_scheduler_latency_score():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    result = sim.compare(snapshot)
    
    # Astra should have equal or better latency score
    cfs_latency = result["linux_cfs"]["latency_score"]
    astra_latency = result["astra_scheduler"]["latency_score"]
    
    assert astra_latency >= cfs_latency


def test_scheduler_timeline():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    result = sim.compare(snapshot)
    
    cfs_timeline = result["linux_cfs"]["timeline"]
    astra_timeline = result["astra_scheduler"]["timeline"]
    
    assert len(cfs_timeline) == result["process_count"]
    assert len(astra_timeline) == result["process_count"]
    
    # Check timeline structure
    for item in cfs_timeline:
        assert "pid" in item
        assert "process" in item
        assert "core" in item
        assert "load" in item


def test_scheduler_single_core():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    snapshot["cpu"]["logical_cores"] = 1
    snapshot["cpu"]["physical_cores"] = 1
    
    result = sim.compare(snapshot)
    assert result["cores"] == 1


def test_scheduler_many_cores():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    snapshot["cpu"]["logical_cores"] = 16
    snapshot["cpu"]["physical_cores"] = 8
    
    result = sim.compare(snapshot)
    assert result["cores"] == 16


def test_scheduler_no_processes():
    sim = SchedulerSimulator()
    snapshot = sample_snapshot()
    snapshot["processes"]["top"] = []
    
    result = sim.compare(snapshot)
    assert result["process_count"] == 0
