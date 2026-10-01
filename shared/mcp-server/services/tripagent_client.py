import os
from typing import Any

import requests


DEFAULT_TIMEOUT = 10


SERVICE_URLS = {
    "account": os.getenv(
        "ACCOUNT_SERVICE_URL",
        "http://localhost:5001",
    ),
    "accommodation": os.getenv(
        "ACCOMMODATION_SERVICE_URL",
        "http://localhost:5002",
    ),
    "attractions": os.getenv(
        "ATTRACTIONS_SERVICE_URL",
        "http://localhost:5003",
    ),
    "checklist": os.getenv(
        "CHECKLIST_SERVICE_URL",
        "http://localhost:5004",
    ),
    "flight": os.getenv(
        "FLIGHT_SERVICE_URL",
        "http://localhost:5005",
    ),
}


class TripAgentServiceError(Exception):
    """Raised when a TripAgent service request fails."""


def get_service_url(service_name: str) -> str:
    """
    Return the configured URL for a TripAgent service.
    """

    service_name = service_name.strip().lower()

    if service_name not in SERVICE_URLS:
        raise TripAgentServiceError(
            f"Unknown TripAgent service: {service_name}"
        )

    return SERVICE_URLS[service_name].rstrip("/")


def request_service(
    service_name: str,
    method: str,
    path: str,
    *,
    customer_id: int | None = None,
    json: dict | None = None,
) -> Any:
    """
    Send an HTTP request to a TripAgent feature service.
    """

    base_url = get_service_url(service_name)

    headers = {}

    if customer_id is not None:
        headers["X-Customer-ID"] = str(customer_id)

    url = f"{base_url}/{path.lstrip('/')}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json,
            timeout=DEFAULT_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise TripAgentServiceError(
            f"{service_name} service request failed: {exc}"
        ) from exc

    if not response.content:
        return {}

    try:
        return response.json()

    except ValueError:
        return {
            "status_code": response.status_code,
            "text": response.text,
        }


def check_service_health(service_name: str) -> dict:
    """
    Check whether a TripAgent feature service is available.
    """

    try:
        base_url = get_service_url(service_name)

        response = requests.get(
            f"{base_url}/health",
            timeout=DEFAULT_TIMEOUT,
        )

        return {
            "service": service_name,
            "available": response.ok,
            "status_code": response.status_code,
        }

    except TripAgentServiceError as exc:
        return {
            "service": service_name,
            "available": False,
            "status_code": None,
            "error": str(exc),
        }

    except requests.RequestException as exc:
        return {
            "service": service_name,
            "available": False,
            "status_code": None,
            "error": str(exc),
        }


def check_all_services() -> dict:
    """
    Check all registered TripAgent feature services.
    """

    results = {}

    for service_name in SERVICE_URLS:
        results[service_name] = check_service_health(
            service_name
        )

    return results


def list_services() -> list[dict]:
    """
    Return all TripAgent services known to the shared MCP server.
    """

    return [
        {
            "id": "account",
            "name": "Account",
            "url": SERVICE_URLS["account"],
        },
        {
            "id": "accommodation",
            "name": "Accommodation",
            "url": SERVICE_URLS["accommodation"],
        },
        {
            "id": "attractions",
            "name": "Attractions",
            "url": SERVICE_URLS["attractions"],
        },
        {
            "id": "checklist",
            "name": "Checklist",
            "url": SERVICE_URLS["checklist"],
        },
        {
            "id": "flight",
            "name": "Flight",
            "url": SERVICE_URLS["flight"],
        },
    ]