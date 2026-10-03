import os
import requests


FLIGHT_DATABASE_URL = os.getenv(
    "FLIGHT_DATABASE_URL",
    "http://localhost:6005",
)

DEFAULT_TIMEOUT = 10


def get_flights(
    origin: str | None = None,
    destination: str | None = None,
) -> list:
    params = {}

    if origin:
        params["origin"] = origin

    if destination:
        params["destination"] = destination

    response = requests.get(
        f"{FLIGHT_DATABASE_URL}/flights",
        params=params,
        timeout=DEFAULT_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


def get_flight_by_id(
    flight_id: int,
) -> dict | None:
    response = requests.get(
        f"{FLIGHT_DATABASE_URL}/flights/{flight_id}",
        timeout=DEFAULT_TIMEOUT,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json()


def get_flights_by_route(
    origin: str,
    destination: str,
) -> list:
    return get_flights(
        origin=origin,
        destination=destination,
    )


def check_service_health() -> dict:
    response = requests.get(
        f"{FLIGHT_DATABASE_URL}/health",
        timeout=5,
    )

    response.raise_for_status()

    return response.json()
