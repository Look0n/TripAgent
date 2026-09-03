from unittest.mock import Mock, patch

import pytest
import requests

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


def make_database_response(payload, status_code=200):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload
    return response


def sample_item(item_id=1):
    return {
        "item_id": item_id,
        "title": "Passport",
        "item_type": "packing",
        "category": "Documents",
        "description": "Bring a valid passport",
        "priority": "High",
        "is_completed": 0
    }


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "healthy",
        "service": "checklist-backend"
    }


def test_get_checklist_items_with_filters(client):
    items = [sample_item()]

    with patch(
        "routes.normal_ui.database_api.get_checklist_items",
        return_value=make_database_response(items)
    ) as get_items:
        response = client.get(
            "/api/checklist-items"
            "?item_type=packing"
            "&category=Documents"
            "&priority=High"
            "&is_completed=false"
        )

    assert response.status_code == 200
    assert response.get_json() == items
    get_items.assert_called_once_with({
        "item_type": "packing",
        "category": "Documents",
        "priority": "High",
        "is_completed": "false"
    })


def test_get_checklist_item_by_id(client):
    item = sample_item()

    with patch(
        "routes.normal_ui.database_api.get_checklist_item",
        return_value=make_database_response(item)
    ) as get_item:
        response = client.get("/api/checklist-items/1")

    assert response.status_code == 200
    assert response.get_json() == item
    get_item.assert_called_once_with(1)


def test_get_nonexistent_checklist_item(client):
    error = {
        "error": "Checklist item not found"
    }

    with patch(
        "routes.normal_ui.database_api.get_checklist_item",
        return_value=make_database_response(error, 404)
    ):
        response = client.get("/api/checklist-items/999")

    assert response.status_code == 404
    assert response.get_json() == error


def test_create_checklist_item(client):
    payload = {
        "title": "Download Offline Maps",
        "item_type": "task",
        "category": "Preparation",
        "description": "Download maps before departure",
        "priority": "Medium",
        "is_completed": False
    }

    created_item = {
        **payload,
        "item_id": 11,
        "is_completed": 0
    }

    with patch(
        "routes.normal_ui.database_api.create_checklist_item",
        return_value=make_database_response(created_item, 201)
    ) as create_item:
        response = client.post(
            "/api/checklist-items",
            json=payload
        )

    assert response.status_code == 201
    assert response.get_json() == created_item
    create_item.assert_called_once_with(payload)


def test_create_checklist_item_requires_json_object(client):
    with patch(
        "routes.normal_ui.database_api.create_checklist_item"
    ) as create_item:
        response = client.post(
            "/api/checklist-items",
            json=["not", "an", "object"]
        )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "A JSON object is required"
    )
    create_item.assert_not_called()


def test_database_validation_error_is_forwarded(client):
    database_error = {
        "error": "Invalid checklist item",
        "fields": {
            "title": "Title is required"
        }
    }

    with patch(
        "routes.normal_ui.database_api.create_checklist_item",
        return_value=make_database_response(database_error, 400)
    ):
        response = client.post(
            "/api/checklist-items",
            json={
                "item_type": "task"
            }
        )

    assert response.status_code == 400
    assert response.get_json() == database_error


def test_update_checklist_item(client):
    payload = {
        "title": "Updated Passport",
        "is_completed": True
    }

    updated_item = {
        **sample_item(),
        "title": "Updated Passport",
        "is_completed": 1
    }

    with patch(
        "routes.normal_ui.database_api.update_checklist_item",
        return_value=make_database_response(updated_item)
    ) as update_item:
        response = client.put(
            "/api/checklist-items/1",
            json=payload
        )

    assert response.status_code == 200
    assert response.get_json() == updated_item
    update_item.assert_called_once_with(1, payload)


def test_update_checklist_item_rejects_empty_object(client):
    with patch(
        "routes.normal_ui.database_api.update_checklist_item"
    ) as update_item:
        response = client.put(
            "/api/checklist-items/1",
            json={}
        )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "A non-empty JSON object is required"
    )
    update_item.assert_not_called()


def test_delete_checklist_item(client):
    database_result = {
        "message": "Checklist item deleted successfully"
    }

    with patch(
        "routes.normal_ui.database_api.delete_checklist_item",
        return_value=make_database_response(database_result)
    ) as delete_item:
        response = client.delete("/api/checklist-items/1")

    assert response.status_code == 200
    assert response.get_json() == database_result
    delete_item.assert_called_once_with(1)


def test_database_unavailable_returns_503(client):
    with patch(
        "routes.normal_ui.database_api.get_checklist_items",
        side_effect=requests.ConnectionError
    ):
        response = client.get("/api/checklist-items")

    assert response.status_code == 503
    assert response.get_json()["error"] == (
        "Checklist database service is unavailable"
    )


def test_invalid_database_response_returns_502(client):
    database_response = Mock()
    database_response.json.side_effect = ValueError

    with patch(
        "routes.normal_ui.database_api.get_checklist_items",
        return_value=database_response
    ):
        response = client.get("/api/checklist-items")

    assert response.status_code == 502
    assert response.get_json()["error"] == (
        "Invalid response from checklist database"
    )
