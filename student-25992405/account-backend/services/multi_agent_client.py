"""HTTP client for the shared, host-run multi-agent server."""
import os
import requests

BASE_URL = os.getenv("MULTI_AGENT_SERVICE_URL", "http://host.docker.internal:7003").rstrip("/")
TIMEOUT = float(os.getenv("MULTI_AGENT_SERVICE_TIMEOUT_SECONDS", "12"))

class MultiAgentClientError(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code

def call_server(method, path, *, params=None, payload=None):
    headers = {}
    key = os.getenv("MULTI_AGENT_API_KEY", "")
    if key:
        headers["X-Multi-Agent-Key"] = key
    try:
        response = requests.request(method, f"{BASE_URL}{path}", params=params,
                                    json=payload, headers=headers, timeout=TIMEOUT)
        try:
            data = response.json()
        except ValueError:
            raise MultiAgentClientError("Multi-Agent server returned invalid JSON")
        if not response.ok:
            raise MultiAgentClientError(data.get("error", "Multi-Agent request failed"), response.status_code)
        return data
    except requests.RequestException as exc:
        raise MultiAgentClientError("Cannot connect to the local Multi-Agent Server") from exc
