from backend.astraos.digital_twin import DigitalTwin


def sample_history(count=10):
    history = []
    for i in range(count):
        history.append({
            "timestamp": float(i),
            "cpu": {"usage_percent": 50.0 + i * 2},
            "memory": {"percent": 60.0 + i},
            "thermal": {"hottest_c": 45.0 + i * 0.5},
        })
    return history


def test_digital_twin_insufficient_data():
    twin = DigitalTwin()
    result = twin.project([], 60)
    
    assert result["status"] == "warming_up"
    assert result["states"] == []


def test_digital_twin_projection():
    twin = DigitalTwin()
    history = sample_history(10)
    result = twin.project(history, 60)
    
    assert result["status"] == "live"
    assert "horizon_seconds" in result
    assert "states" in result
    assert "recommended_strategy" in result
    assert result["horizon_seconds"] == 60


def test_digital_twin_states():
    twin = DigitalTwin()
    history = sample_history(10)
    result = twin.project(history, 30)
    
    states = result["states"]
    assert len(states) > 0
    assert all("t_plus_seconds" in state for state in states)
    assert all("cpu_percent" in state for state in states)
    assert all("memory_percent" in state for state in states)
    assert all("risk" in state for state in states)


def test_digital_twin_risk_assessment():
    twin = DigitalTwin()
    history = sample_history(10)
    result = twin.project(history, 30)
    
    states = result["states"]
    assert all(state["risk"] in {"normal", "warning", "critical"} for state in states)


def test_digital_twin_critical_risk():
    twin = DigitalTwin()
    history = sample_history(10)
    # Create high pressure scenario
    for item in history:
        item["cpu"]["usage_percent"] = 95.0
        item["memory"]["percent"] = 95.0
        item["thermal"]["hottest_c"] = 95.0
    
    result = twin.project(history, 30)
    states = result["states"]
    assert any(state["risk"] == "critical" for state in states)


def test_digital_twin_warning_risk():
    twin = DigitalTwin()
    history = sample_history(10)
    # Create moderate pressure scenario
    for item in history:
        item["cpu"]["usage_percent"] = 85.0
        item["memory"]["percent"] = 85.0
        item["thermal"]["hottest_c"] = 85.0
    
    result = twin.project(history, 30)
    states = result["states"]
    assert any(state["risk"] == "warning" for state in states)


def test_digital_twin_normal_risk():
    twin = DigitalTwin()
    history = sample_history(10)
    # Create normal scenario
    for item in history:
        item["cpu"]["usage_percent"] = 40.0
        item["memory"]["percent"] = 50.0
        item["thermal"]["hottest_c"] = 60.0
    
    result = twin.project(history, 30)
    states = result["states"]
    assert all(state["risk"] == "normal" for state in states)


def test_digital_twin_strategy():
    twin = DigitalTwin()
    history = sample_history(10)
    result = twin.project(history, 30)
    
    strategy = result["recommended_strategy"]
    assert strategy in {"observe", "watch_and_prepare_optimization", "preemptive_rebalance_and_throttle"}


def test_digital_twin_horizon_clamping():
    twin = DigitalTwin()
    history = sample_history(10)
    
    # Test minimum horizon
    result = twin.project(history, 1)
    assert result["horizon_seconds"] >= 5
    
    # Test maximum horizon
    result = twin.project(history, 1000)
    assert result["horizon_seconds"] <= 600


def test_digital_twin_temperature_forecasting():
    twin = DigitalTwin()
    history = sample_history(10)
    result = twin.project(history, 30)
    
    states = result["states"]
    # Check that temperature is forecasted when available
    if history[0]["thermal"]["hottest_c"]:
        assert all("temperature_c" in state for state in states)
