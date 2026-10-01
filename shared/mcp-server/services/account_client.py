"""Client for the existing TripAgent Account backend.

The MCP server runs on the host machine. The Account backend is published by
Docker on localhost:5001, so this client deliberately calls the backend rather
than accessing the Account SQLite database directly.
"""

import os
from typing import Any

import requests


ACCOUNT_BACKEND_URL = os.getenv(
    "ACCOUNT_BACKEND_URL",
    "http://localhost:5001",
).rstrip("/")

DEFAULT_TIMEOUT = 10


class AccountServiceError(RuntimeError):
    """Raised when the Account backend cannot complete an MCP request."""


def _request(
    method: str,
    path: str,
    *,
    customer_id: int | None = None,
    json_data: dict | None = None,
) -> Any:
    headers = {}

    # The existing Account backend already trusts X-Customer-ID forwarded by
    # the shared gateway. The MCP integration reuses the same convention.
    if customer_id is not None:
        headers["X-Customer-ID"] = str(customer_id)

    try:
        response = requests.request(
            method=method,
            url=f"{ACCOUNT_BACKEND_URL}{path}",
            headers=headers,
            json=json_data,
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise AccountServiceError(
            "Account backend is unavailable"
        ) from exc

    try:
        payload = response.json() if response.content else {}
    except ValueError:
        payload = {
            "error": "Account backend returned a non-JSON response"
        }

    if not response.ok:
        message = payload.get(
            "error",
            f"Account backend returned HTTP {response.status_code}",
        )
        raise AccountServiceError(message)

    return payload


def get_profile(customer_id: int) -> dict:
    """Get the current customer's profile through the existing backend."""
    return _request(
        "GET",
        "/api/account/profile",
        customer_id=customer_id,
    )


def get_preferences(customer_id: int) -> dict:
    """Get the current customer's preferences through the existing backend."""
    return _request(
        "GET",
        "/api/account/preferences",
        customer_id=customer_id,
    )


def update_preferences(customer_id: int, preferences: dict) -> dict:
    """Update the current customer's preferences through the backend."""
    return _request(
        "PUT",
        "/api/account/preferences",
        customer_id=customer_id,
        json_data=preferences,
    )


def check_health() -> dict:
    """Return the health of the existing Account backend."""
    try:
        response = requests.get(
            f"{ACCOUNT_BACKEND_URL}/health",
            timeout=DEFAULT_TIMEOUT,
        )
        payload = response.json() if response.content else {}
        return {
            "available": response.ok,
            "status_code": response.status_code,
            "details": payload,
        }
    except (requests.RequestException, ValueError):
        return {
            "available": False,
            "status_code": None,
            "details": {},
        }
