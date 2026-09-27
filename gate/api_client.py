"""请求封装：门禁对后端 API 的全部 HTTP 调用都经过这里（仅用标准库）。"""
import json
import urllib.error
import urllib.request


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise ApiError(f"{method} {path} -> {e.code}: {e.read().decode(errors='replace')}") from e
        except urllib.error.URLError as e:
            raise ApiError(f"{method} {path} -> {e.reason}") from e

    def get(self, path):
        return self._request("GET", path)

    def put(self, path, body):
        return self._request("PUT", path, body)

    def health(self):
        return self.get("/api/health")

    def list_windows(self):
        return self.get("/api/windows")["items"]

    def list_fabrics(self):
        return self.get("/api/fabrics")["items"]

    def get_window(self, wid):
        return self.get(f"/api/windows/{wid}")

    def get_fabric(self, fid):
        return self.get(f"/api/fabrics/{fid}")

    def dry_run(self, window_id, fabric_id):
        return self.get(f"/api/estimate?window_id={window_id}&fabric_id={fabric_id}")

    def update_window(self, wid, **fields):
        return self.put(f"/api/windows/{wid}", fields)

    def update_fabric(self, fid, **fields):
        return self.put(f"/api/fabrics/{fid}", fields)
