import os

import requests


FLIGHT_DATABASE_URL = os.getenv(
    "FLIGHT_DATABASE_URL",
    "http://flight-database:6005"
)

DEFAULT_TIMEOUT = 5


def list_flights(origin=None, destination=None):
    params = {}

    if origin:
        params["origin"] = origin

    if destination:
        params["destination"] = destination

    return requests.get(
        f"{FLIGHT_DATABASE_URL}/flights",
        params=params,
        timeout=DEFAULT_TIMEOUT
    )

  


def get_flight(flight_id):
    return requests.get(
        f"{FLIGHT_DATABASE_URL}/flights/{flight_id}",
        timeout=DEFAULT_TIMEOUT
    )


def create_flight(data):
    return requests.post(
        f"{FLIGHT_DATABASE_URL}/flights",
        json=data,
        timeout=DEFAULT_TIMEOUT
    )


def update_flight(flight_id, data):
    return requests.put(
        f"{FLIGHT_DATABASE_URL}/flights/{flight_id}",
        json=data,
        timeout=DEFAULT_TIMEOUT
    )


def delete_flight(flight_id):
    return requests.delete(
        f"{FLIGHT_DATABASE_URL}/flights/{flight_id}",
        timeout=DEFAULT_TIMEOUT
    )