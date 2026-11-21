import json
import pytest
from compiler.middleware import RateLimiter, validate_input, JSONFormatter, setup_logging
from app import app


class TestRateLimiter:
    def test_allows_first_request(self):
        limiter = RateLimiter(requests_per_minute=10)
        assert limiter.is_allowed("test1") is True

    def test_blocks_after_limit(self):
        limiter = RateLimiter(requests_per_minute=3)
        assert limiter.is_allowed("test2") is True
        assert limiter.is_allowed("test2") is True
        assert limiter.is_allowed("test2") is True
        assert limiter.is_allowed("test2") is False

    def test_different_keys_independent(self):
        limiter = RateLimiter(requests_per_minute=2)
        assert limiter.is_allowed("a") is True
        assert limiter.is_allowed("a") is True
        assert limiter.is_allowed("a") is False
        assert limiter.is_allowed("b") is True


class TestValidateInput:
    def test_valid_logic_passes(self):
        assert validate_input({"logic": "IF aTc -> GFP"}) == []

    def test_logic_too_long(self):
        long_str = "A" * 10001
        errors = validate_input({"logic": long_str})
        assert len(errors) >= 1
        assert "10000" in errors[0]

    def test_logic_must_be_string(self):
        errors = validate_input({"logic": 123})
        assert len(errors) >= 1

    def test_nodes_must_be_array(self):
        errors = validate_input({"nodes": "not_array"})
        assert len(errors) >= 1

    def test_parts_too_many(self):
        errors = validate_input({"parts": list(range(501))})
        assert len(errors) >= 1


class TestJSONFormatter:
    def test_formatter_outputs_json(self):
        import logging
        formatter = JSONFormatter()
        record = logging.LogRecord("test", logging.INFO, "", 0,
                                   "hello world", None, None)
        output = formatter.format(record)
        data = json.loads(output)
        assert data["message"] == "hello world"
        assert data["level"] == "INFO"
        assert data["logger"] == "test"


class TestRateLimitEndpoint:
    @pytest.fixture
    def client(self):
        app.config["TESTING"] = True
        with app.test_client() as c:
            yield c

    def test_health_not_rate_limited(self, client):
        for _ in range(5):
            resp = client.get("/api/health")
            assert resp.status_code == 200

    def test_compile_returns_json_on_success(self, client):
        resp = client.post("/api/compile",
                           json={"logic": "IF aTc -> GFP"},
                           content_type="application/json")
        data = json.loads(resp.data)
        assert "success" in data
