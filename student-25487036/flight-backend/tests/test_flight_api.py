"""Post-commit CI/CD endpoint tests for two Flight backend/API functions.

Endpoint function 1: list_flights   - GET  /api/flight/flights
Endpoint function 2: create_flight  - POST /api/flight/flights

The flight database service is stubbed so these tests verify the backend's own
request handling, status mapping and failure behaviour without depending on
another container being reachable from the CI runner.
"""
from unittest.mock import Mock

import pytest
import requests

from app import app
from routes import normal_ui


BASE = "/api/flight/flights"

SAMPLE_FLIGHT = {
    "flight_id": 2,
    "airline": "Jetstar",
    "origin": "SYD",
    "destination": "MEL",
    "departure_time": "2026-09-15T11:20:00",
    "arrival_time": "2026-09-15T13:00:00",
    "duration": 100,
    "price": 109.0,
    "seat_availability": 64,
}


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def stub_response(payload, status_code=200):
    response = Mock()
    response.json = Mock(return_value=payload)
    response.status_code = status_code
    return response


def test_list_flights_returns_records_from_database_service(client, monkeypatch):
    stub = Mock(return_value=stub_response([SAMPLE_FLIGHT]))
    monkeypatch.setattr(normal_ui.database_api, "list_flights", stub)

    response = client.get(BASE)

    assert response.status_code == 200
    assert response.get_json() == [SAMPLE_FLIGHT]
    stub.assert_called_once_with(None, None)


def test_list_flights_forwards_route_filters(client, monkeypatch):
    stub = Mock(return_value=stub_response([SAMPLE_FLIGHT]))
    monkeypatch.setattr(normal_ui.database_api, "list_flights", stub)

    response = client.get(f"{BASE}?origin=SYD&destination=MEL")

    assert response.status_code == 200
    stub.assert_called_once_with("SYD", "MEL")


def test_list_flights_returns_503_when_database_unavailable(client, monkeypatch):
    stub = Mock(side_effect=requests.RequestException("connection refused"))
    monkeypatch.setattr(normal_ui.database_api, "list_flights", stub)

    response = client.get(BASE)

    assert response.status_code == 503
    assert response.get_json()["error"] == "Flight database unavailable"


def test_create_flight_forwards_payload_and_returns_201(client, monkeypatch):
    created = dict(SAMPLE_FLIGHT, flight_id=13)
    stub = Mock(return_value=stub_response(created, 201))
    monkeypatch.setattr(normal_ui.database_api, "create_flight", stub)

    payload = {
        "airline": "Qantas",
        "origin": "SYD",
        "destination": "BNE",
        "departure_time": "2026-11-01T08:00:00",
        "arrival_time": "2026-11-01T09:30:00",
        "price": 180.0,
        "seat_availability": 42,
    }

    response = client.post(BASE, json=payload)

    assert response.status_code == 201
    assert response.get_json()["flight_id"] == 13
    stub.assert_called_once_with(payload)


def test_create_flight_propagates_duplicate_conflict(client, monkeypatch):
    stub = Mock(return_value=stub_response(
        {"error": "Flight already exists"}, 409
    ))
    monkeypatch.setattr(normal_ui.database_api, "create_flight", stub)

    response = client.post(BASE, json={"airline": "Qantas"})

    assert response.status_code == 409
    assert "error" in response.get_json()


def test_create_flight_returns_503_when_database_unavailable(client, monkeypatch):
    stub = Mock(side_effect=requests.RequestException("connection refused"))
    monkeypatch.setattr(normal_ui.database_api, "create_flight", stub)

    response = client.post(BASE, json={"airline": "Qantas"})

    assert response.status_code == 503
    assert response.get_json()["error"] == "Flight database unavailable"
