import json
import os
import requests

MULTI_AGENT_SERVICE_URL = os.getenv("MULTI_AGENT_SERVICE_URL", "http://localhost:7003",).rstrip("/")

MULTI_AGENT_TIMEOUT_SECONDS = float(os.getenv("MULTI_AGENT_SERVICE_TIMEOUT_SECONDS", "12"))

class MultiAgentClientError(RuntimeError):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code

def is_multi_agent_enabled():
    enabled = os.getenv("MULTI_AGENT_ENABLED", "false").lower() in ("true", "1", "yes", "on")

    locked = os.getenv("MULTI_AGENT_LOCKED", "false").lower() in ("true", "1", "yes", "on")

    return enabled and not locked

def call_server(method, path, params=None, payload=None):
    if not is_multi_agent_enabled():
        raise MultiAgentClientError("Multi-agent mode is disabled", 403)

    if payload is not None and len(json.dumps(payload).encode("utf-8")) > 24000:
        raise MultiAgentClientError("The workflow request is too large", 413)

    headers = {}

    api_key = os.getenv("MULTI_AGENT_API_KEY", "")

    if api_key:
        headers["X-Multi-Agent-Key"] = api_key

    try:
        response = requests.request(
            method = method,
            url = f"{MULTI_AGENT_SERVICE_URL}{path}",
            params = params,
            json = payload,
            headers = headers,
            timeout = (3, MULTI_AGENT_TIMEOUT_SECONDS)
        )
    except requests.Timeout as exc:
        raise MultiAgentClientError("Multi-agent server request timed out", 504) from exc

    except requests.RequestException as exc:
        raise MultiAgentClientError("Multi-Agent server is unavailable") from exc

    try:
        result = response.json()

    except ValueError as exc:
        raise MultiAgentClientError("Multi-Agent server returned invalid JSON", 502) from exc

    if not isinstance(result, dict):
        raise MultiAgentClientError("Multi-Agent server returned an invalid response", 502)

    if not response.ok:
        message = result.get("error")

        if not isinstance(message, str) or not message.strip():
            message = "Multi-Agent request falied"

        raise MultiAgentClientError(message, response.status_code)

    return result