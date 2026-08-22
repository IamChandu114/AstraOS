from backend.astraos.healing import SelfHealingEngine


def sample_history(count=10):
    history = []
    for i in range(count):
        history.append({
            "timestamp": float(i),
            "cpu": {"usage_percent": 50.0 + i * 2},
            "memory": {"percent": 60.0 + i},
            "thermal": {"hottest_c": 45.0 + i * 0.5},
            "processes": {
                "total": 10,
                "top": [
                    {"pid": 1001, "name": "python", "cpu_percent": 15.0 + i, "memory_percent": 5.0, "nice": 0},
                    {"pid": 1002, "name": "chrome", "cpu_percent": 12.0, "memory_percent": 8.0, "nice": 0},
                ],
            },
        })
    return history


def test_healing_insufficient_data():
    healer = SelfHealingEngine()
    result = healer.evaluate([], None)
    
    assert result["status"] == "warming_up"
    assert result["incidents"] == []
    assert result["recovery_plan"] == []


def test_healing_normal_conditions():
    healer = SelfHealingEngine()
    history = sample_history(10)
    result = healer.evaluate(history, None)
    
    assert result["status"] == "live"
    assert "incidents" in result
    assert "recovery_plan" in result
    assert "timeline" in result


def test_healing_high_cpu_incident():
    healer = SelfHealingEngine()
    history = sample_history(10)
    # Add a high CPU process
    history[-1]["processes"]["top"].append({
        "pid": 9999,
        "name": "stress",
        "cpu_percent": 90.0,
        "memory_percent": 5.0,
        "nice": 0,
    })
    result = healer.evaluate(history, None)
    
    assert result["status"] == "live"
    incidents = result["incidents"]
    assert len(incidents) > 0
    assert any(inc["type"] == "runaway_cpu" for inc in incidents)


def test_healing_memory_pressure():
    healer = SelfHealingEngine()
    history = sample_history(10)
    # Set high memory
    history[-1]["memory"]["percent"] = 92.0
    result = healer.evaluate(history, None)
    
    assert result["status"] == "live"
    incidents = result["incidents"]
    assert any(inc["type"] == "system_memory_pressure" for inc in incidents)


def test_healing_anomaly_detection():
    healer = SelfHealingEngine()
    history = sample_history(20)
    prediction = {"anomaly": {"is_anomaly": True, "score": 0.85}}
    result = healer.evaluate(history, prediction)
    
    assert result["status"] == "live"
    incidents = result["incidents"]
    assert any(inc["type"] == "resource_anomaly" for inc in incidents)


def test_healing_recovery_plan():
    healer = SelfHealingEngine()
    history = sample_history(10)
    result = healer.evaluate(history, None)
    
    recovery_plan = result["recovery_plan"]
    assert isinstance(recovery_plan, list)
    assert len(recovery_plan) == len(result["incidents"])


def test_healing_timeline():
    healer = SelfHealingEngine()
    history = sample_history(10)
    result = healer.evaluate(history, None)
    
    timeline = result["timeline"]
    assert isinstance(timeline, list)
    assert all("timestamp" in item for item in timeline)
    assert all("event" in item for item in timeline)
    assert all("severity" in item for item in timeline)
