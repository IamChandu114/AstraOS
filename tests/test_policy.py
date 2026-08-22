from backend.astraos.policy import OptimizationPolicy


def sample_snapshot(cpu=70.0, memory=70.0):
    return {
        "timestamp": 1.0,
        "cpu": {"usage_percent": cpu, "logical_cores": 8, "physical_cores": 4},
        "memory": {"percent": memory},
        "thermal": {"hottest_c": 65.0},
        "processes": {
            "total": 10,
            "top": [
                {"pid": 1001, "name": "python", "cpu_percent": 15.0, "memory_percent": 5.0, "nice": 0},
                {"pid": 1002, "name": "chrome", "cpu_percent": 12.0, "memory_percent": 8.0, "nice": 0},
            ],
        },
    }


def test_policy_plan_generation():
    policy = OptimizationPolicy()
    snapshot = sample_snapshot(cpu=80.0, memory=75.0)
    plan = policy.plan(snapshot, None)
    
    assert "timestamp" in plan
    assert "plan_id" in plan
    assert "mode" in plan
    assert "actions" in plan
    assert "protected_processes" in plan
    assert "policy" in plan
    assert plan["mode"] == "plan"


def test_policy_high_cpu():
    policy = OptimizationPolicy()
    snapshot = sample_snapshot(cpu=85.0, memory=70.0)
    plan = policy.plan(snapshot, None)
    
    assert len(plan["actions"]) > 0
    assert any(action["type"] == "cpu_affinity" for action in plan["actions"])


def test_policy_high_memory():
    policy = OptimizationPolicy()
    snapshot = sample_snapshot(cpu=60.0, memory=85.0)
    plan = policy.plan(snapshot, None)
    
    assert len(plan["actions"]) > 0
    assert any(action["type"] == "memory_pressure" for action in plan["actions"])


def test_policy_normal_conditions():
    policy = OptimizationPolicy()
    snapshot = sample_snapshot(cpu=40.0, memory=50.0)
    plan = policy.plan(snapshot, None)
    
    assert len(plan["actions"]) > 0
    assert plan["actions"][0]["type"] == "observe"


def test_policy_protected_processes():
    policy = OptimizationPolicy()
    snapshot = sample_snapshot(cpu=80.0, memory=70.0)
    plan = policy.plan(snapshot, None)
    
    assert "protected_processes" in plan
    assert isinstance(plan["protected_processes"], list)


def test_policy_apply_without_enable():
    import os
    policy = OptimizationPolicy()
    snapshot = sample_snapshot(cpu=80.0, memory=70.0)
    plan = policy.plan(snapshot, None)
    
    # Ensure ASTRAOS_ENABLE_APPLY is not set
    if "ASTRAOS_ENABLE_APPLY" in os.environ:
        del os.environ["ASTRAOS_ENABLE_APPLY"]
    
    result = policy.apply(plan)
    
    assert result["mode"] == "blocked"
    assert "message" in result
    assert result["rollback_plan"] == []


def test_policy_rollback():
    policy = OptimizationPolicy()
    rollback_plan = [
        {"type": "renice", "pid": 1001, "nice": 0},
        {"type": "cpu_affinity", "pid": 1002, "cores": [0, 1, 2, 3]},
    ]
    
    result = policy.rollback(rollback_plan)
    
    assert "timestamp" in result
    assert "mode" in result
    assert result["mode"] == "rollback"
    assert "results" in result


def test_policy_structure():
    policy = OptimizationPolicy()
    snapshot = sample_snapshot()
    plan = policy.plan(snapshot, None)
    
    assert plan["policy"]["protected_mode"] == True
    assert plan["policy"]["rollback_supported"] == True
    assert plan["policy"]["apply_gate"] == "ASTRAOS_ENABLE_APPLY=1"
    assert plan["requires_apply_enabled"] == True
