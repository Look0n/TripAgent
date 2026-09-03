import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_get_all_accommodations(client):

    response = client.get(
        "/api/accommodations"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, list)


def test_get_accommodation_by_id(client):

    response = client.get(
        "/api/accommodations/1"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert "accommodation_id" in data
    assert "accommodation_name" in data


def test_search_accommodations(client):

    response = client.get(
        "/api/accommodations"
        "?city=Sydney"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert isinstance(data, list)

    for accommodation in data:
        assert (
            accommodation["city"]
            == "Sydney"
        )
        

def test_create_accommodation(client):

    payload = {
        "accommodation_name": "Test Hotel",
        "type": "Hotel",
        "city": "Sydney",
        "address": "123 Test Street",
        "price_per_night": 250,
        "guest_capacity": 2,
        "rating": 4.2,
        "description": "Test accommodation",
        "image_url": "static/images/test.png"
    }

    response = client.post(
        "/api/accommodations",
        json=payload
    )

    assert response.status_code in [200, 201]

    data = response.get_json()

    assert data is not None
    
    
def test_update_accommodation(client):

    payload = {
        "accommodation_name": "Updated Test Hotel",
        "type": "Hotel",
        "city": "Sydney",
        "address": "456 Updated Street",
        "price_per_night": 280,
        "guest_capacity": 3,
        "rating": 4.5,
        "description": "Updated accommodation",
        "image_url": "static/images/test.png"
    }

    response = client.put(
        "/api/accommodations/1",
        json=payload
    )

    assert response.status_code == 200
    
    
def test_delete_accommodation(client):

    payload = {
        "accommodation_name": "Delete Test Hotel",
        "type": "Hotel",
        "city": "Sydney",
        "address": "Delete Street",
        "price_per_night": 200,
        "guest_capacity": 2,
        "rating": 4.0,
        "description": "Temporary test",
        "image_url": "static/images/test.png"
    }

    create_response = client.post(
        "/api/accommodations",
        json=payload
    )

    created = create_response.get_json()

    accommodation_id = (
        created.get("accommodation_id")
        or created.get("id")
    )

    assert accommodation_id is not None

    delete_response = client.delete(
        f"/api/accommodations/{accommodation_id}"
    )

    assert delete_response.status_code == 200
    
    
def test_availability_available(client):

    response = client.get(
        "/api/accommodations/1/availability"
        "?check_in=2026-09-05"
        "&check_out=2026-09-06"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "available"
    assert data["available"] is True
    
    
def test_availability_unavailable(client):

    response = client.get(
        "/api/accommodations/1/availability"
        "?check_in=2026-09-05"
        "&check_out=2026-09-07"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "unavailable"
    assert data["available"] is False
    assert "2026-09-06" in data["unavailable_dates"]
    
    
def test_availability_unknown(client):

    response = client.get(
        "/api/accommodations/1/availability"
        "?check_in=2026-09-20"
        "&check_out=2026-09-22"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "unknown"
    assert data["available"] is None