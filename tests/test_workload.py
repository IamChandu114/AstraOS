from backend.astraos.workload import WorkloadClassifier


def sample_snapshot():
    return {
        "timestamp": 1.0,
        "cpu": {"usage_percent": 70.0},
        "memory": {"percent": 60.0},
        "network": {"bytes_recv_per_sec": 1000.0},
        "gpu": {"devices": []},
        "processes": {
            "total": 10,
            "top": [
                {"pid": 1001, "name": "python", "cpu_percent": 25.0, "memory_percent": 5.0, "nice": 0},
                {"pid": 1002, "name": "chrome", "cpu_percent": 20.0, "memory_percent": 8.0, "nice": 0},
            ],
        },
    }


def test_workload_classification():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    result = classifier.classify(snapshot)
    
    assert "category" in result
    assert "confidence" in result
    assert "scores" in result
    assert "evidence" in result
    assert "policy_profile" in result


def test_workload_category():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    result = classifier.classify(snapshot)
    
    category = result["category"]
    assert isinstance(category, str)
    assert len(category) > 0
    assert category in classifier.KEYWORDS or category == "balanced"


def test_workload_confidence():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    result = classifier.classify(snapshot)
    
    confidence = result["confidence"]
    assert 0.0 <= confidence <= 1.0
    assert isinstance(confidence, float)


def test_workload_scores():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    result = classifier.classify(snapshot)
    
    scores = result["scores"]
    assert isinstance(scores, dict)
    assert all(key in classifier.KEYWORDS for key in scores.keys())
    assert all(isinstance(score, (int, float)) for score in scores.values())


def test_workload_gaming_detection():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    snapshot["processes"]["top"].append({
        "pid": 9999,
        "name": "steam",
        "cpu_percent": 30.0,
        "memory_percent": 10.0,
        "nice": 0,
    })
    snapshot["gpu"]["devices"] = [{"utilization_percent": 80.0}]
    result = classifier.classify(snapshot)
    
    assert result["category"] in {"gaming", "ai_inference", "balanced"}


def test_workload_ai_inference_detection():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    snapshot["processes"]["top"].append({
        "pid": 9999,
        "name": "python",
        "cpu_percent": 40.0,
        "memory_percent": 15.0,
        "nice": 0,
    })
    snapshot["gpu"]["devices"] = [{"utilization_percent": 90.0}]
    result = classifier.classify(snapshot)
    
    assert result["category"] in {"ai_inference", "gaming", "balanced"}


def test_workload_browser_heavy_detection():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    snapshot["processes"]["top"] = [
        {"pid": 1001, "name": "chrome", "cpu_percent": 30.0, "memory_percent": 15.0, "nice": 0},
        {"pid": 1002, "name": "firefox", "cpu_percent": 25.0, "memory_percent": 12.0, "nice": 0},
    ]
    result = classifier.classify(snapshot)
    
    assert result["category"] in {"browser_heavy", "balanced"}


def test_workload_compiler_heavy_detection():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    snapshot["cpu"]["usage_percent"] = 85.0
    snapshot["memory"]["percent"] = 75.0
    snapshot["processes"]["top"].append({
        "pid": 9999,
        "name": "gcc",
        "cpu_percent": 50.0,
        "memory_percent": 10.0,
        "nice": 0,
    })
    result = classifier.classify(snapshot)
    
    assert result["category"] in {"compiler_heavy", "balanced"}


def test_workload_policy_profile():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    result = classifier.classify(snapshot)
    
    policy = result["policy_profile"]
    assert isinstance(policy, dict)
    assert "priority" in policy


def test_workload_evidence():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    result = classifier.classify(snapshot)
    
    evidence = result["evidence"]
    assert isinstance(evidence, dict)
    assert all(isinstance(evidence[key], list) for key in evidence.keys())


def test_workload_protected_process_exclusion():
    classifier = WorkloadClassifier()
    snapshot = sample_snapshot()
    # Add protected process
    snapshot["processes"]["top"].append({
        "pid": 1,
        "name": "systemd",
        "cpu_percent": 5.0,
        "memory_percent": 2.0,
        "nice": 0,
    })
    result = classifier.classify(snapshot)
    
    # Should not crash and should still produce valid results
    assert result["category"] in classifier.KEYWORDS or result["category"] == "balanced"


def test_workload_keywords():
    classifier = WorkloadClassifier()
    assert len(classifier.KEYWORDS) > 0
    assert "gaming" in classifier.KEYWORDS
    assert "ai_inference" in classifier.KEYWORDS
    assert "browser_heavy" in classifier.KEYWORDS


def test_workload_policy_for_all_categories():
    classifier = WorkloadClassifier()
    for category in classifier.KEYWORDS:
        policy = classifier.policy_for(category)
        assert isinstance(policy, dict)
        assert "priority" in policy
