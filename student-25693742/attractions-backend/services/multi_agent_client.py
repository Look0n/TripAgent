# Multi-Agent client for the Attractions backend.
# The shared Multi-Agent Server runs on the host machine (not in Docker),
# so we reach it via host.docker.internal from inside the container.

import os

import requests


MULTI_AGENT_SERVICE_URL = os.getenv(
    "MULTI_AGENT_SERVICE_URL",
    "http://host.docker.internal:7003",
).rstrip("/")

TIMEOUT = float(
    os.getenv("MULTI_AGENT_SERVICE_TIMEOUT_SECONDS", "15")
)


class MultiAgentClientError(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code


# One HTTP call to the Multi-Agent Server.
# Sends the shared API key header when MULTI_AGENT_API_KEY is configured.
def call_server(method, path, params=None, payload=None):
    headers = {}

    api_key = os.getenv("MULTI_AGENT_API_KEY", "")

    if api_key:
        headers["X-Multi-Agent-Key"] = api_key

    try:
        response = requests.request(
            method,
            f"{MULTI_AGENT_SERVICE_URL}{path}",
            params=params,
            json=payload,
            headers=headers,
            timeout=TIMEOUT,
        )

    except requests.RequestException as exc:
        raise MultiAgentClientError(
            "Multi-Agent Server unavailable."
        ) from exc

    try:
        data = response.json()

    except ValueError as exc:
        raise MultiAgentClientError(
            "Multi-Agent Server returned invalid JSON."
        ) from exc

    if not response.ok:
        raise MultiAgentClientError(
            data.get("error", "Multi-Agent request failed."),
            response.status_code,
        )

    return data


# Quick check that the Multi-Agent Server is reachable.
def check_multi_agent_health():
    try:
        data = call_server("GET", "/health")

    except MultiAgentClientError as exc:
        return {
            "status": "error",
            "error": str(exc),
        }

    return {
        "status": "connected",
        "features": data.get("features", []),
    }
