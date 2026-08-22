from backend.astraos.predictive_alerts import PredictiveAlertEngine


def sample_history(count=8):
    return [
        {
            "timestamp": float(index),
            "cpu": {"usage_percent": 54.0 + index * 4},
            "memory": {"percent": 62.0 + index},
            "thermal": {"hottest_c": 48.0 + index},
            "disk": {"root_percent": 71.0},
            "network": {"bytes_recv_per_sec": 1024.0 * 1024.0, "bytes_sent_per_sec": 512.0 * 1024.0},
            "processes": {
                "total": 220,
                "states": {"running": 6, "disk_sleep": 2},
                "top": [{"pid": 4242, "name": "benchmark", "cpu_percent": 74.0, "memory_percent": 7.2}],
            },
        }
        for index in range(count)
    ]


def test_predictive_alert_payload_contains_production_sections():
    engine = PredictiveAlertEngine()
    prediction = {
        "cpu_spike": {"forecast_6s": 94.0, "risk": "critical", "confidence": 0.91},
        "memory_pressure": {"forecast_6s": 80.0, "risk": "normal", "confidence": 0.72},
        "thermal": {"forecast_6s": 76.0, "risk": "normal", "confidence": 0.7},
    }

    result = engine.generate(sample_history(), prediction, {"findings": []})

    assert result["status"] == "live"
    assert result["alerts"]
    assert result["reliability_index"]["score"] <= 100
    assert result["prevention_counter"]["incidents_avoided"] >= 1
    assert result["copilot"]["recommended_fix"]
    assert [step["stage"] for step in result["demo_flow"]] == ["Observe", "Predict", "Decide", "Act", "Verify"]


def test_predictive_alert_engine_detects_process_instability():
    engine = PredictiveAlertEngine()

    result = engine.generate(sample_history(), None, {"findings": []})

    assert any(alert["affected_resource"] == "process_instability" for alert in result["alerts"])
