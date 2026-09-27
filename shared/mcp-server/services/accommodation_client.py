import os
import requests


ACCOMMODATION_DATABASE_URL = os.getenv(
    "ACCOMMODATION_DATABASE_URL",
    "http://localhost:6002",
)


def get_accommodations() -> list:
    response = requests.get(
        f"{ACCOMMODATION_DATABASE_URL}/accommodations",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_accommodation_by_city(
    city: str,
) -> list:
    response = requests.get(
        f"{ACCOMMODATION_DATABASE_URL}/accommodations",
        params={
            "city": city,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def search_accommodations(
    city: str,
    max_price: float | None = None,
    guests: int | None = None,
    type: str | None = None,
) -> list:
    params = {
        "city": city,
    }

    if max_price is not None:
        params["max_price"] = max_price

    if guests is not None:
        params["guests"] = guests
    
    if type:
        params["type"] = type

    response = requests.get(
        f"{ACCOMMODATION_DATABASE_URL}/accommodations",
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def check_accommodation_availability(
    accommodation_id: int,
    check_in: str,
    check_out: str,
) -> dict:
    response = requests.get(
        (
            f"{ACCOMMODATION_DATABASE_URL}"
            f"/availability/{accommodation_id}"
        ),
        params={
            "check_in": check_in,
            "check_out": check_out,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()