"""Release 2 post-commit CI/CD tests for two Attractions endpoint functions.

Endpoint function 1: list attractions   - GET  /api/attractions
Endpoint function 2: create attraction  - POST /api/attractions

The attractions database service is stubbed, so these tests check the
backend's own request handling, validation, status codes and failure
behaviour without needing the database container on the CI runner.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock

import pytest
import requests

from app import app as flask_app
from routes import normal_ui


BASE = "/api/attractions"

SAMPLE_ATTRACTION = {
    "attraction_id": 1,
    "name": "Eiffel Tower Summit Tour",
    "category": "Sightseeing",
    "city": "Paris",
    "price": 45.0,
    "average_rating": 4.8,
}


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Endpoint function 1: GET /api/attractions
# ---------------------------------------------------------------------------

def test_list_attractions_returns_records(client, monkeypatch):
    stub = Mock(return_value=[SAMPLE_ATTRACTION])
    monkeypatch.setattr(normal_ui, "get_all_attractions", stub)

    response = client.get(BASE)

    assert response.status_code == 200
    assert response.get_json() == [SAMPLE_ATTRACTION]
    stub.assert_called_once_with(
        search=None, city=None, category=None, max_price=None
    )


def test_list_attractions_forwards_filters(client, monkeypatch):
    stub = Mock(return_value=[SAMPLE_ATTRACTION])
    monkeypatch.setattr(normal_ui, "get_all_attractions", stub)

    response = client.get(
        f"{BASE}?search=tower&city=Paris&category=Sightseeing&max_price=50"
    )

    assert response.status_code == 200
    stub.assert_called_once_with(
        search="tower", city="Paris", category="Sightseeing", max_price=50.0
    )


def test_list_attractions_rejects_non_numeric_max_price(client, monkeypatch):
    stub = Mock()
    monkeypatch.setattr(normal_ui, "get_all_attractions", stub)

    response = client.get(f"{BASE}?max_price=cheap")

    assert response.status_code == 400
    assert response.get_json()["error"] == "max_price must be a number"
    stub.assert_not_called()


def test_list_attractions_returns_503_when_database_unavailable(client, monkeypatch):
    stub = Mock(side_effect=requests.RequestException("connection refused"))
    monkeypatch.setattr(normal_ui, "get_all_attractions", stub)

    response = client.get(BASE)

    assert response.status_code == 503
    assert response.get_json()["error"] == "Database service unavailable"


# ---------------------------------------------------------------------------
# Endpoint function 2: POST /api/attractions
# ---------------------------------------------------------------------------

NEW_ATTRACTION = {
    "name": "Harbour Kayak Tour",
    "category": "Adventure",
    "city": "Sydney",
    "price": 60,
    "description": "Paddle around the harbour with a local guide.",
}


def test_create_attraction_returns_201(client, monkeypatch):
    created = dict(NEW_ATTRACTION, attraction_id=11)
    stub = Mock(return_value=created)
    monkeypatch.setattr(normal_ui, "create_attraction", stub)

    response = client.post(BASE, json=NEW_ATTRACTION)

    assert response.status_code == 201
    assert response.get_json() == created
    stub.assert_called_once_with(NEW_ATTRACTION)


@pytest.mark.parametrize("missing", ["name", "category", "city", "price"])
def test_create_attraction_requires_fields(client, monkeypatch, missing):
    stub = Mock()
    monkeypatch.setattr(normal_ui, "create_attraction", stub)

    payload = {k: v for k, v in NEW_ATTRACTION.items() if k != missing}
    response = client.post(BASE, json=payload)

    assert response.status_code == 400
    assert response.get_json()["error"] == f"Missing required field: {missing}"
    stub.assert_not_called()


@pytest.mark.parametrize(
    "price, message",
    [("free", "price must be a number"), (-5, "price must not be negative")],
)
def test_create_attraction_validates_price(client, monkeypatch, price, message):
    stub = Mock()
    monkeypatch.setattr(normal_ui, "create_attraction", stub)

    response = client.post(BASE, json=dict(NEW_ATTRACTION, price=price))

    assert response.status_code == 400
    assert response.get_json()["error"] == message
    stub.assert_not_called()


def test_create_attraction_returns_503_when_database_unavailable(client, monkeypatch):
    stub = Mock(side_effect=requests.RequestException("connection refused"))
    monkeypatch.setattr(normal_ui, "create_attraction", stub)

    response = client.post(BASE, json=NEW_ATTRACTION)

    assert response.status_code == 503
    assert response.get_json()["error"] == "Database service unavailable"
