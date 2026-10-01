import os
import requests


DATABASE_API_URL = os.getenv(
    "DATABASE_API_URL",
    "http://127.0.0.1:6003"
)


def get_all_attractions(
    search=None,
    city=None,
    category=None,
    max_price=None
):
    params = {}

    if search:
        params["search"] = search

    if city:
        params["city"] = city

    if category:
        params["category"] = category

    if max_price is not None:
        params["max_price"] = max_price

    response = requests.get(
        f"{DATABASE_API_URL}/attractions",
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_attraction_by_id(attraction_id):
    response = requests.get(
        f"{DATABASE_API_URL}/attractions/{attraction_id}",
        timeout=10
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json()


def create_attraction(data):
    response = requests.post(
        f"{DATABASE_API_URL}/attractions",
        json=data,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def update_attraction(attraction_id, data):
    response = requests.put(
        f"{DATABASE_API_URL}/attractions/{attraction_id}",
        json=data,
        timeout=10
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json()


def delete_attraction(attraction_id):
    response = requests.delete(
        f"{DATABASE_API_URL}/attractions/{attraction_id}",
        timeout=10
    )

    if response.status_code == 404:
        return False

    response.raise_for_status()

    return True


def get_reviews(attraction_id):
    response = requests.get(
        f"{DATABASE_API_URL}/attractions/{attraction_id}/reviews",
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def create_review(attraction_id, data):
    response = requests.post(
        f"{DATABASE_API_URL}/attractions/{attraction_id}/reviews",
        json=data,
        timeout=10
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    return response.json()


def search_for_recommendation(
    city=None,
    category=None,
    max_price=None,
    limit=5
):
    attractions = get_all_attractions(
        city=city,
        category=category,
        max_price=max_price
    )

    attractions.sort(
        key=lambda item: item.get("average_rating") or 0,
        reverse=True
    )

    return attractions[:limit]
