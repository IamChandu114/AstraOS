from backend.astraos.thermal import ThermalForecaster


def sample_history(count=10):
    history = []
    for i in range(count):
        history.append({
            "timestamp": float(i),
            "thermal": {"hottest_c": 45.0 + i * 0.5},
            "gpu": {"devices": []},
        })
    return history


def test_thermal_forecast_unavailable():
    forecaster = ThermalForecaster()
    result = forecaster.forecast([])
    
    assert result["status"] == "unavailable"
    assert "message" in result
    assert result["heatmap"] == []


def test_thermal_forecast_with_cpu_data():
    forecaster = ThermalForecaster()
    history = sample_history(10)
    result = forecaster.forecast(history)
    
    assert result["status"] == "live"
    assert "current_c" in result
    assert "forecast_30s_c" in result
    assert "slope_c_per_sample" in result
    assert "risk" in result
    assert "cooling_efficiency" in result
    assert "heatmap" in result


def test_thermal_forecast_with_gpu_data():
    forecaster = ThermalForecaster()
    history = []
    for i in range(10):
        history.append({
            "timestamp": float(i),
            "thermal": {"hottest_c": None},
            "gpu": {"devices": [{"temperature_c": 50.0 + i * 0.3}]},
        })
    result = forecaster.forecast(history)
    
    assert result["status"] == "live"
    assert result["current_c"] is not None


def test_thermal_risk_assessment():
    forecaster = ThermalForecaster()
    history = sample_history(10)
    result = forecaster.forecast(history)
    
    risk = result["risk"]
    assert risk in {"normal", "warning", "critical"}


def test_thermal_critical_risk():
    forecaster = ThermalForecaster()
    history = []
    for i in range(10):
        history.append({
            "timestamp": float(i),
            "thermal": {"hottest_c": 85.0 + i * 0.5},
            "gpu": {"devices": []},
        })
    result = forecaster.forecast(history)
    
    assert result["risk"] == "critical"


def test_thermal_warning_risk():
    forecaster = ThermalForecaster()
    history = []
    for i in range(10):
        history.append({
            "timestamp": float(i),
            "thermal": {"hottest_c": 80.0 + i * 0.2},
            "gpu": {"devices": []},
        })
    result = forecaster.forecast(history)
    
    assert result["risk"] == "warning"


def test_thermal_normal_risk():
    forecaster = ThermalForecaster()
    history = []
    for i in range(10):
        history.append({
            "timestamp": float(i),
            "thermal": {"hottest_c": 50.0 + i * 0.1},
            "gpu": {"devices": []},
        })
    result = forecaster.forecast(history)
    
    assert result["risk"] == "normal"


def test_thermal_slope_calculation():
    forecaster = ThermalForecaster()
    history = sample_history(10)
    result = forecaster.forecast(history)
    
    slope = result["slope_c_per_sample"]
    assert isinstance(slope, float)


def test_thermal_cooling_efficiency():
    forecaster = ThermalForecaster()
    history = sample_history(10)
    result = forecaster.forecast(history)
    
    efficiency = result["cooling_efficiency"]
    assert 0.0 <= efficiency <= 1.0


def test_thermal_heatmap():
    forecaster = ThermalForecaster()
    history = sample_history(10)
    result = forecaster.forecast(history)
    
    heatmap = result["heatmap"]
    assert isinstance(heatmap, list)
    assert len(heatmap) == 64  # 8x8 grid
    
    # Check heatmap structure
    for cell in heatmap:
        assert "row" in cell
        assert "col" in cell
        assert "temperature_c" in cell
        assert "risk" in cell
        assert cell["risk"] in {"hot", "warm", "normal"}


def test_thermal_forecast_clamping():
    forecaster = ThermalForecaster()
    # Test with extreme temperatures
    history = []
    for i in range(10):
        history.append({
            "timestamp": float(i),
            "thermal": {"hottest_c": 200.0 + i * 10},
            "gpu": {"devices": []},
        })
    result = forecaster.forecast(history)
    
    # Forecast should be clamped to reasonable range
    assert result["forecast_30s_c"] <= 125.0


def test_thermal_forecast_negative_clamping():
    forecaster = ThermalForecaster()
    # Test with negative temperatures
    history = []
    for i in range(10):
        history.append({
            "timestamp": float(i),
            "thermal": {"hottest_c": -30.0 + i * 2},
            "gpu": {"devices": []},
        })
    result = forecaster.forecast(history)
    
    # Forecast should be clamped to reasonable range
    assert result["forecast_30s_c"] >= -20.0
