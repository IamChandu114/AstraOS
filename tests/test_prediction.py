from backend.astraos.prediction import RealTelemetryPredictor


def sample_history(count=10):
    history = []
    for i in range(count):
        history.append({
            "timestamp": float(i),
            "cpu": {"usage_percent": 50.0 + i * 2},
            "memory": {"percent": 60.0 + i},
            "thermal": {"hottest_c": 45.0 + i * 0.5},
            "swap": {"percent": 10.0},
            "network": {"bytes_recv_per_sec": 1000.0 * i},
            "gpu": {"devices": []},
        })
    return history


def test_predictor_insufficient_data():
    predictor = RealTelemetryPredictor()
    result = predictor.predict([])
    
    assert result["status"] == "insufficient_live_telemetry"
    assert "message" in result


def test_predictor_with_history():
    predictor = RealTelemetryPredictor()
    history = sample_history(20)
    result = predictor.predict(history)
    
    assert result["status"] == "live"
    assert "cpu_spike" in result
    assert "thermal" in result
    assert "memory_pressure" in result
    assert "power" in result
    assert "anomaly" in result
    assert "workload_class" in result
    assert "recommendations" in result


def test_predictor_cpu_forecast():
    predictor = RealTelemetryPredictor()
    history = sample_history(20)
    result = predictor.predict(history)
    
    cpu_forecast = result["cpu_spike"]
    assert "current" in cpu_forecast
    assert "forecast_6s" in cpu_forecast
    assert "risk" in cpu_forecast
    assert "confidence" in cpu_forecast
    assert cpu_forecast["risk"] in {"normal", "warning", "critical"}


def test_predictor_thermal_forecast():
    predictor = RealTelemetryPredictor()
    history = sample_history(20)
    result = predictor.predict(history)
    
    thermal_forecast = result["thermal"]
    assert "current" in thermal_forecast
    assert "forecast_6s" in thermal_forecast
    assert "risk" in thermal_forecast
    assert thermal_forecast["risk"] in {"normal", "warning", "critical"}


def test_predictor_memory_forecast():
    predictor = RealTelemetryPredictor()
    history = sample_history(20)
    result = predictor.predict(history)
    
    memory_forecast = result["memory_pressure"]
    assert "current" in memory_forecast
    assert "forecast_6s" in memory_forecast
    assert "forecast_60s" in memory_forecast
    assert "risk_score" in memory_forecast
    assert "expected_failure_time" in memory_forecast
    assert "reasoning" in memory_forecast
    assert "risk" in memory_forecast


def test_predictor_anomaly_detection():
    predictor = RealTelemetryPredictor()
    history = sample_history(30)
    result = predictor.predict(history)
    
    anomaly = result["anomaly"]
    assert "score" in anomaly
    assert "is_anomaly" in anomaly
    assert isinstance(anomaly["score"], float)


def test_predictor_workload_classification():
    predictor = RealTelemetryPredictor()
    history = sample_history(20)
    result = predictor.predict(history)
    
    workload = result["workload_class"]
    assert isinstance(workload, str)
    assert len(workload) > 0


def test_predictor_recommendations():
    predictor = RealTelemetryPredictor()
    history = sample_history(20)
    result = predictor.predict(history)
    
    recommendations = result["recommendations"]
    assert isinstance(recommendations, list)
