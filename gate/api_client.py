"""请求封装 — thin JSON-over-HTTP client used by the gate entry.

Stdlib only (urllib) so the gate runs with zero extra dependencies.
"""
import json
import urllib.error
import urllib.request


class ApiError(RuntimeError):
    """HTTP call failed or returned a non-2xx status."""

    def __init__(self, method: str, path: str, status: int, body: str):
        super().__init__(f"{method} {path} -> {status}: {body}")
        self.status = status
        self.body = body


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise ApiError(method, path, e.code, e.read().decode("utf-8", "replace")) from None
        except urllib.error.URLError as e:
            raise ApiError(method, path, 0, str(e)) from None

    def get(self, path: str):
        return self._request("GET", path)

    def put(self, path: str, payload: dict):
        return self._request("PUT", path, payload)

    def post(self, path: str, payload: dict):
        return self._request("POST", path, payload)
