import time
import json
import logging
from functools import wraps
from flask import request, jsonify, current_app


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        return json.dumps(log_entry)


def setup_logging(app):
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    app.logger.handlers = []
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self._requests_per_minute = requests_per_minute
        self._clients = {}

    def _cleanup(self):
        now = time.time()
        cutoff = now - 60
        expired = [k for k, v in self._clients.items() if v[-1] < cutoff]
        for k in expired:
            del self._clients[k]

    def is_allowed(self, key):
        self._cleanup()
        now = time.time()
        if key not in self._clients:
            self._clients[key] = []
        timestamps = self._clients[key]
        timestamps[:] = [t for t in timestamps if t > now - 60]
        if len(timestamps) >= self._requests_per_minute:
            return False
        timestamps.append(now)
        return True


_GLOBAL_LIMITER = RateLimiter(requests_per_minute=60)


def rate_limit(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        client_ip = request.remote_addr or "unknown"
        if not _GLOBAL_LIMITER.is_allowed(client_ip):
            app = current_app._get_current_object()
            app.logger.warning("Rate limit exceeded", extra={"request_id": id(request)})
            return jsonify({
                "success": False,
                "error": "Rate limit exceeded. Try again later."
            }), 429
        return f(*args, **kwargs)
    return wrapper


def _validate_list_field(payload, key, max_items):
    value = payload.get(key)
    if value is not None:
        if not isinstance(value, list):
            return [f"'{key}' must be an array"]
        if len(value) > max_items:
            return [f"'{key}' exceeds {max_items} item limit"]
    return []


def _validate_number_field(payload, key, lo=None, hi=None):
    value = payload.get(key)
    if value is not None:
        if not isinstance(value, (int, float)):
            return [f"'{key}' must be a number"]
        if lo is not None and value < lo:
            return [f"'{key}' must be >= {lo}"]
        if hi is not None and value > hi:
            return [f"'{key}' must be <= {hi}"]
    return []


def validate_input(payload):
    errors = []
    for key in ("logic",):
        value = payload.get(key)
        if value is not None:
            if not isinstance(value, str):
                errors.append(f"'{key}' must be a string")
            elif len(value) > 10000:
                errors.append(f"'{key}' exceeds 10000 character limit")

    errors.extend(_validate_list_field(payload, "nodes", 500))
    errors.extend(_validate_list_field(payload, "edges", 500))
    errors.extend(_validate_list_field(payload, "parts", 500))

    t_span = payload.get("t_span")
    if t_span is not None:
        if not isinstance(t_span, (list, tuple)) or len(t_span) != 2:
            errors.append("'t_span' must be an array of 2 numbers [start, end]")
        else:
            for i, v in enumerate(t_span):
                if not isinstance(v, (int, float)):
                    errors.append(f"'t_span[{i}]' must be a number")

    errors.extend(_validate_number_field(payload, "dt", lo=0))
    errors.extend(_validate_number_field(payload, "pop_size", lo=1, hi=10000))
    errors.extend(_validate_number_field(payload, "generations", lo=1, hi=10000))
    errors.extend(_validate_number_field(payload, "target_output", lo=0))

    inputs = payload.get("inputs")
    if inputs is not None and not isinstance(inputs, dict):
        errors.append("'inputs' must be an object")

    params = payload.get("params")
    if params is not None and not isinstance(params, dict):
        errors.append("'params' must be an object")

    return errors
