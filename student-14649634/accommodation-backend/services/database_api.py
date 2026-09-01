import os
import requests


DATABASE_API_URL = os.getenv(
    "DATABASE_API_URL",
    "http://127.0.0.1:6002"
)


def get_all_accommodations(
    city=None,
    accommodation_type=None,
    max_price=None
):
    params = {}

    if city:
        params["city"] = city

    if accommodation_type:
        params["type"] = accommodation_type

    if max_price is not None:
        params["max_price"] = max_price

    response = requests.get(
        f"{DATABASE_API_URL}/accommodations",
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_accommodation_by_id(accommodation_id):
    response = requests.get(
        f"{DATABASE_API_URL}/accommodations/{accommodation_id}",
        timeout=10
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json()


def create_accommodation(data):
    response = requests.post(
        f"{DATABASE_API_URL}/accommodations",
        json=data,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def update_accommodation(accommodation_id, data):
    response = requests.put(
        f"{DATABASE_API_URL}/accommodations/{accommodation_id}",
        json=data,
        timeout=10
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json()


def delete_accommodation(accommodation_id):
    response = requests.delete(
        f"{DATABASE_API_URL}/accommodations/{accommodation_id}",
        timeout=10
    )

    if response.status_code == 404:
        return False

    response.raise_for_status()

    return True


def search_for_recommendation(
    city=None,
    budget=None,
    guests=None,
    accommodation_type=None
):
    params = {}

    if city:
        params["city"] = city

    if budget is not None:
        params["max_price"] = budget

    if guests is not None:
        params["guests"] = guests

    if accommodation_type:
        params["type"] = accommodation_type

    response = requests.get(
        f"{DATABASE_API_URL}/accommodations",
        params=params,
        timeout=10
    )

    response.raise_for_status()

    accommodations = response.json()

    accommodations.sort(
        key=lambda item: item.get("rating") or 0,
        reverse=True
    )

    return accommodations[:2]