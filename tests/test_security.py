from backend.astraos.security import SecurityAnalyzer


def sample_snapshot():
    return {
        "timestamp": 1.0,
        "cpu": {"usage_percent": 50.0},
        "memory": {"percent": 60.0},
        "network": {"bytes_recv_per_sec": 1000.0, "bytes_sent_per_sec": 500.0},
        "processes": {
            "total": 10,
            "top": [
                {"pid": 1001, "name": "python", "cpu_percent": 15.0, "memory_percent": 5.0, "nice": 0},
                {"pid": 1002, "name": "chrome", "cpu_percent": 12.0, "memory_percent": 8.0, "nice": 0},
            ],
        },
    }


def test_security_normal_conditions():
    analyzer = SecurityAnalyzer()
    snapshot = sample_snapshot()
    result = analyzer.analyze(snapshot, None)
    
    assert "timestamp" in result
    assert "risk_score" in result
    assert "risk_level" in result
    assert "alerts" in result
    assert result["risk_level"] in {"low", "medium", "high"}


def test_security_suspicious_process():
    analyzer = SecurityAnalyzer()
    snapshot = sample_snapshot()
    # Add a suspicious process
    snapshot["processes"]["top"].append({
        "pid": 9999,
        "name": "xmrig",
        "cpu_percent": 20.0,
        "memory_percent": 5.0,
        "nice": 0,
    })
    result = analyzer.analyze(snapshot, None)
    
    assert result["risk_score"] >= 40
    assert len(result["alerts"]) > 0
    assert any(alert["type"] == "suspicious_process_resource_use" for alert in result["alerts"])


def test_security_extreme_cpu():
    analyzer = SecurityAnalyzer()
    snapshot = sample_snapshot()
    # Add extreme CPU process
    snapshot["processes"]["top"].append({
        "pid": 9999,
        "name": "test",
        "cpu_percent": 98.0,
        "memory_percent": 5.0,
        "nice": 0,
    })
    result = analyzer.analyze(snapshot, None)
    
    assert len(result["alerts"]) > 0
    assert any(alert["type"] == "extreme_cpu_process" for alert in result["alerts"])


def test_security_abnormal_network():
    analyzer = SecurityAnalyzer()
    snapshot = sample_snapshot()
    # Set abnormal network volume
    snapshot["network"]["bytes_recv_per_sec"] = 60_000_000.0
    snapshot["network"]["bytes_sent_per_sec"] = 10_000_000.0
    result = analyzer.analyze(snapshot, None)
    
    assert len(result["alerts"]) > 0
    assert any(alert["type"] == "abnormal_network_volume" for alert in result["alerts"])


def test_security_anomaly_detection():
    analyzer = SecurityAnalyzer()
    snapshot = sample_snapshot()
    prediction = {"anomaly": {"is_anomaly": True, "score": 0.85}}
    result = analyzer.analyze(snapshot, prediction)
    
    assert len(result["alerts"]) > 0
    assert any(alert["type"] == "ai_resource_anomaly" for alert in result["alerts"])


def test_security_risk_score_calculation():
    analyzer = SecurityAnalyzer()
    snapshot = sample_snapshot()
    result = analyzer.analyze(snapshot, None)
    
    assert 0 <= result["risk_score"] <= 100
    assert isinstance(result["risk_score"], (int, float))


def test_security_matches_suspicious_name():
    analyzer = SecurityAnalyzer()
    
    assert analyzer._matches_suspicious_name("xmrig") == True
    assert analyzer._matches_suspicious_name("miner.exe") == True
    assert analyzer._matches_suspicious_name("python") == False
    assert analyzer._matches_suspicious_name("chrome") == False


def test_security_protected_process_exclusion():
    analyzer = SecurityAnalyzer()
    snapshot = sample_snapshot()
    # Add a protected process (system)
    snapshot["processes"]["top"].append({
        "pid": 1,
        "name": "systemd",
        "cpu_percent": 5.0,
        "memory_percent": 2.0,
        "nice": 0,
    })
    result = analyzer.analyze(snapshot, None)
    
    # System processes should not trigger alerts
    suspicious_alerts = [alert for alert in result["alerts"] if alert.get("type") == "suspicious_process_resource_use"]
    assert not any(alert["process"]["name"] == "systemd" for alert in suspicious_alerts)
