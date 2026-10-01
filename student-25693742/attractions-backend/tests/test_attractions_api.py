import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True

    with flask_app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["service"] == "attractions-backend"


def test_get_all_attractions(client):
    response = client.get("/api/attractions")

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_get_attraction_not_found(client):
    response = client.get("/api/attractions/999999")

    assert response.status_code == 404


def test_search_attractions(client):
    response = client.get("/api/attractions?search=Paris")

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)
