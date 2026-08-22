from backend.astraos.distributed_sim import DistributedFabric


def test_distributed_fabric_initialization():
    fabric = DistributedFabric()
    assert fabric.started_at > 0
    assert len(fabric.profiles) == 4
    assert fabric._stress == {}


def test_distributed_fabric_snapshot():
    fabric = DistributedFabric()
    snapshot = fabric.snapshot()
    
    assert "timestamp" in snapshot
    assert "cluster" in snapshot
    assert "mode" in snapshot
    assert "node_count" in snapshot
    assert "online" in snapshot
    assert "health_score" in snapshot
    assert "aggregate" in snapshot
    assert "nodes" in snapshot
    assert "orchestration_events" in snapshot
    assert "active_stressors" in snapshot


def test_distributed_fabric_nodes():
    fabric = DistributedFabric()
    snapshot = fabric.snapshot()
    
    nodes = snapshot["nodes"]
    assert len(nodes) == 4
    
    # Check node structure
    for node in nodes:
        assert "name" in node
        assert "role" in node
        assert "workload" in node
        assert "status" in node
        assert "uptime_seconds" in node
        assert "cpu_percent" in node
        assert "memory_percent" in node
        assert "network_mbps" in node
        assert "health_score" in node


def test_distributed_fabric_node_names():
    fabric = DistributedFabric()
    snapshot = fabric.snapshot()
    
    node_names = [node["name"] for node in snapshot["nodes"]]
    expected_names = ["astra-node-1", "astra-node-2", "astra-node-3", "astra-node-4"]
    assert node_names == expected_names


def test_distributed_fabric_aggregate():
    fabric = DistributedFabric()
    snapshot = fabric.snapshot()
    
    aggregate = snapshot["aggregate"]
    assert "cpu_percent" in aggregate
    assert "memory_percent" in aggregate
    assert "network_mbps" in aggregate


def test_distributed_fabric_health_score():
    fabric = DistributedFabric()
    snapshot = fabric.snapshot()
    
    health_score = snapshot["health_score"]
    assert 0 <= health_score <= 100
    assert isinstance(health_score, float)


def test_distributed_fabric_stress_application():
    fabric = DistributedFabric()
    result = fabric.apply_stress("cpu", intensity=1.0, duration_seconds=90)
    
    assert "mode" in result
    assert "intensity" in result
    assert "expires_at" in result
    assert result["mode"] == "cpu"
    assert result["intensity"] == 1.0


def test_distributed_fabric_stress_cpu():
    fabric = DistributedFabric()
    fabric.apply_stress("cpu", intensity=1.0, duration_seconds=90)
    snapshot = fabric.snapshot()
    
    # CPU stress should affect node-1
    node1 = next(node for node in snapshot["nodes"] if node["name"] == "astra-node-1")
    assert node1["cpu_percent"] > 78  # Base is 78, stress adds more


def test_distributed_fabric_stress_memory():
    fabric = DistributedFabric()
    fabric.apply_stress("memory", intensity=1.0, duration_seconds=90)
    snapshot = fabric.snapshot()
    
    # Memory stress should affect node-2
    node2 = next(node for node in snapshot["nodes"] if node["name"] == "astra-node-2")
    assert node2["memory_percent"] > 83  # Base is 83, stress adds more


def test_distributed_fabric_stress_network():
    fabric = DistributedFabric()
    fabric.apply_stress("network", intensity=1.0, duration_seconds=90)
    snapshot = fabric.snapshot()
    
    # Network stress should affect node-3
    node3 = next(node for node in snapshot["nodes"] if node["name"] == "astra-node-3")
    assert node3["network_mbps"] > 76  # Base is 76, stress adds more


def test_distributed_fabric_stress_node_crash():
    fabric = DistributedFabric()
    fabric.apply_stress("node_crash", intensity=1.0, duration_seconds=90)
    snapshot = fabric.snapshot()
    
    # Node crash should affect node-4
    node4 = next(node for node in snapshot["nodes"] if node["name"] == "astra-node-4")
    assert node4["status"] == "degraded"
    assert node4["health_score"] == 28


def test_distributed_fabric_stress_active():
    fabric = DistributedFabric()
    # Apply stress with a duration
    result = fabric.apply_stress("cpu", intensity=1.0, duration_seconds=10)
    
    # Stress should be active
    snapshot = fabric.snapshot()
    active_stressors = snapshot["active_stressors"]
    assert "cpu" in active_stressors
    assert active_stressors["cpu"]["intensity"] == 1.0


def test_distributed_fabric_orchestration_events():
    fabric = DistributedFabric()
    snapshot = fabric.snapshot()
    
    events = snapshot["orchestration_events"]
    assert isinstance(events, list)
    
    # Check event structure
    for event in events:
        assert "timestamp" in event
        assert "source" in event
        assert "target" in event
        assert "action" in event
        assert "confidence" in event


def test_distributed_fabric_intensity_clamping():
    fabric = DistributedFabric()
    
    # Test minimum intensity
    result = fabric.apply_stress("cpu", intensity=0.0, duration_seconds=90)
    assert result["intensity"] >= 0.1
    
    # Test maximum intensity
    result = fabric.apply_stress("cpu", intensity=3.0, duration_seconds=90)
    assert result["intensity"] <= 2.0


def test_distributed_fabric_dominant_pressure():
    fabric = DistributedFabric()
    snapshot = fabric.snapshot()
    
    for node in snapshot["nodes"]:
        assert "dominant_pressure" in node
        assert node["dominant_pressure"] in {"cpu", "memory", "network"}


def test_distributed_fabric_tasks():
    fabric = DistributedFabric()
    snapshot = fabric.snapshot()
    
    for node in snapshot["nodes"]:
        assert "tasks" in node
        assert node["tasks"] >= 1
