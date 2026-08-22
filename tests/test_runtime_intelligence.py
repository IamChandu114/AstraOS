from backend.astraos.incidents import IncidentTimelineEngine
from backend.astraos.proof_engine import OptimizationProofEngine
from backend.astraos.root_cause import RootCauseAnalyzer


def sample_snapshot(cpu=91.0, memory=84.0):
    return {
        "timestamp": 1.0,
        "cpu": {"usage_percent": cpu},
        "memory": {"percent": memory},
        "swap": {"percent": 12.0},
        "thermal": {"hottest_c": None},
        "network": {"bytes_recv_per_sec": 1024, "bytes_sent_per_sec": 2048},
        "processes": {
            "total": 3,
            "top": [
                {"pid": 2001, "name": "python", "cpu_percent": 63.0, "memory_percent": 11.2, "threads": 8},
                {"pid": 2002, "name": "chrome", "cpu_percent": 12.0, "memory_percent": 21.4, "threads": 30},
            ],
        },
    }


def test_root_cause_explains_pressure():
    result = RootCauseAnalyzer().analyze(sample_snapshot(), {"cpu_spike": {"risk": "warning"}})
    assert result["status"] == "live"
    assert result["findings"]
    assert result["findings"][0]["contributors"]
    assert "confidence" in result["findings"][0]


def test_incident_timeline_includes_prediction_phase():
    prediction = {"cpu_spike": {"risk": "warning", "confidence": 0.91}}
    root_cause = RootCauseAnalyzer().analyze(sample_snapshot(), prediction)
    result = IncidentTimelineEngine().build([sample_snapshot()], prediction, [], root_cause)
    assert result["incident_id"].startswith("inc-")
    assert any(item["phase"] in {"prediction", "analysis"} for item in result["timeline"])


def test_optimization_proof_calculates_improvement():
    before = sample_snapshot(cpu=90.0, memory=80.0)
    after = sample_snapshot(cpu=60.0, memory=70.0)
    result = OptimizationProofEngine().summarize({"before": before, "after": after, "execution_id": "exec-test"})
    assert result["status"] == "measured"
    assert result["effectiveness_score"] > 0
    assert result["statements"]
