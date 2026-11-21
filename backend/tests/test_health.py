import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["status"] == "ok"
        assert data["service"] == "cyto-logic-backend"

    def test_health_has_version(self, client):
        resp = client.get("/api/health")
        data = json.loads(resp.data)
        assert "version" in data
