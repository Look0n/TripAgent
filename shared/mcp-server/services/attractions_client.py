# MCP-side HTTP client for the Attractions feature.
# Talks to the attractions-database service over HTTP (same pattern
# as accommodation_client.py / account_client.py in this folder).

import os
import requests


ATTRACTIONS_DATABASE_URL = os.getenv(
    "ATTRACTIONS_DATABASE_URL",
    "http://localhost:6003",
)


def get_attractions() -> list:
    response = requests.get(
        f"{ATTRACTIONS_DATABASE_URL}/attractions",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_attractions_by_city(
    city: str,
) -> list:
    response = requests.get(
        f"{ATTRACTIONS_DATABASE_URL}/attractions",
        params={
            "city": city,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def search_attractions(
    city: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
) -> list:
    params = {}

    if city:
        params["city"] = city

    if category:
        params["category"] = category

    if max_price is not None:
        params["max_price"] = max_price

    response = requests.get(
        f"{ATTRACTIONS_DATABASE_URL}/attractions",
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_attraction_details(
    attraction_id: int,
) -> dict:
    response = requests.get(
        f"{ATTRACTIONS_DATABASE_URL}/attractions/{attraction_id}",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_top_rated_attractions(
    city: str | None = None,
    limit: int = 5,
) -> list:
    params = {}

    if city:
        params["city"] = city

    response = requests.get(
        f"{ATTRACTIONS_DATABASE_URL}/attractions",
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    attractions = response.json()

    attractions.sort(
        key=lambda item: item.get("average_rating") or 0,
        reverse=True,
    )

    return attractions[:limit]
