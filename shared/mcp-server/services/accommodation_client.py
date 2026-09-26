import os
import requests


ACCOMMODATION_DATABASE_URL = os.getenv(
    "ACCOMMODATION_DATABASE_URL",
    "http://localhost:6002",
)


def search_accommodations(
    city: str,
    max_price: float | None = None,
    guests: int | None = None,
) -> list:
    params = {
        "city": city,
    }

    if max_price is not None:
        params["max_price"] = max_price

    if guests is not None:
        params["guests"] = guests

    response = requests.get(
        f"{ACCOMMODATION_DATABASE_URL}/accommodations",
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()