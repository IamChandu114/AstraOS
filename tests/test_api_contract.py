from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_final_runtime_endpoints_exist():
    paths = [
        "/health",
        "/root-cause",
        "/incidents",
        "/optimization/proof",
        "/architecture",
        "/elite/status",
        "/predictive/alerts",
        "/reliability",
        "/executive-summary",
        "/pipeline/debug",
        "/incidents/history",
    ]
    for path in paths:
        response = client.get(path)
        assert response.status_code in {200, 503}


def test_chaos_rejects_unknown_mode():
    response = client.post("/chaos/not-a-mode")
    assert response.status_code == 400


def test_prometheus_endpoint_returns_text():
    response = client.get("/metrics/prometheus")
    assert response.status_code == 200
    assert "astraos" in response.text.lower() or "warming up" in response.text.lower()
