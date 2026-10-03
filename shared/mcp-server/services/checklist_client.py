import os
from typing import Any
import requests

CHECKLIST_BACKEND_URL = os.getenv(
    "CHECKLIST_BACKEND_URL",
    "http://localhost:5004",
).rstrip("/")

DEFAULT_TIMEOUT = 10

class ChecklistServiceError(RuntimeError):
    """Raised when the Checklist backend cannot complete an MCP request."""

def _request(
        method: str,
        path: str,
        *,
        params: dict | None = None,
) -> Any:
    try:
        response = requests.request(
            method=method,
            url=f"{CHECKLIST_BACKEND_URL}{path}",
            params=params,
            timeout=DEFAULT_TIMEOUT,
        )

    except requests.RequestException as exc:
        raise ChecklistServiceError(
            "Checklist backend is unavailable"
        ) from exc

    try:
        payload = response.json()

    except ValueError as exc:
        raise ChecklistServiceError(
            "Checklist backend returned a non-JSON response"
        ) from exc

    if not response.ok:
        message = (
            f"Checklist backend returned HTTP {response.status_code} "
        )

        if isinstance(payload, dict):
            error = payload.get("error")

            if isinstance(error, str) and error.strip():
                message = error

        raise ChecklistServiceError(message)

    return payload

def get_items(
        params: dict | None = None,
) -> list:
    items = _request(
        "GET",
        "/api/checklist-items",
        params=params,
    )

    if not isinstance(items, list) or not all(
        isinstance(item, dict) for item in items
    ):
        raise ChecklistServiceError(
            "Checklist backend returned an invalid response"
        )

    return items

def get_item(
        item_id: int,
) -> dict:
    item =_request(
        "GET",
        f"/api/checklist-items/{item_id}",
    )

    if not isinstance(item, dict) or item.get("item_id") != item_id:
        raise ChecklistServiceError(
            "Checklist backend returned an invalid item"
        )

    return item

