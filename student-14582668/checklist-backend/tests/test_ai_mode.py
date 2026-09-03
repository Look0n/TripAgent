import json
from unittest.mock import Mock, patch

import requests

from app import app


def make_database_response(items, status_code=200):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = items
    return response


def test_ai_recommendation_success_and_no_automatic_save():
    existing_items = [
        {
            "item_id": 1,
            "title": "Passport",
            "item_type": "packing",
            "category": "Documents",
            "description": "Bring a valid passport",
            "priority": "High",
            "is_completed": 0
        }
    ]

    ai_response = json.dumps({
        "reply": "Consider these additional items.",
        "suggestions": [
            {
                "title": "Passport",
                "item_type": "packing",
                "category": "Documents",
                "description": "Duplicate item",
                "priority": "High"
            },
            {
                "title": "Download Offline Maps",
                "item_type": "task",
                "category": "Preparation",
                "description": "Download maps before departure",
                "priority": "Medium"
            }
        ]
    })

    with patch(
        "routes.ai_mode.database_api.get_checklist_items",
        return_value=make_database_response(existing_items)
    ), patch(
        "routes.ai_mode.generate_text",
        return_value=ai_response
    ), patch(
        "routes.ai_mode.database_api.create_checklist_item"
    ) as create_item:
        response = app.test_client().post(
            "/api/checklist-items/recommend",
            json={
                "message": "I am travelling to Japan for seven days."
            }
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["existing_items_count"] == 1
    assert data["reply"] == "Consider these additional items."
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["title"] == (
        "Download Offline Maps"
    )
    assert data["suggestions"][0]["item_type"] == "task"
    assert data["suggestions"][0]["priority"] == "Medium"
    create_item.assert_not_called()


def test_ai_recommendation_requires_message():
    response = app.test_client().post(
        "/api/checklist-items/recommend",
        json={}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Message is required"


def test_ai_recommendation_handles_database_unavailable():
    with patch(
        "routes.ai_mode.database_api.get_checklist_items",
        side_effect=requests.ConnectionError
    ):
        response = app.test_client().post(
            "/api/checklist-items/recommend",
            json={
                "message": "What should I prepare for my trip?"
            }
        )

    assert response.status_code == 503
    assert response.get_json()["error"] == (
        "Checklist database service is unavailable"
    )


def test_ai_recommendation_handles_ollama_unavailable():
    with patch(
        "routes.ai_mode.database_api.get_checklist_items",
        return_value=make_database_response([])
    ), patch(
        "routes.ai_mode.generate_text",
        side_effect=requests.Timeout
    ):
        response = app.test_client().post(
            "/api/checklist-items/recommend",
            json={
                "message": "What should I prepare for my trip?"
            }
        )

    assert response.status_code == 503
    assert response.get_json()["error"] == (
        "AI service is currently unavailable"
    )


def test_ai_recommendation_rejects_invalid_ai_json():
    with patch(
        "routes.ai_mode.database_api.get_checklist_items",
        return_value=make_database_response([])
    ), patch(
        "routes.ai_mode.generate_text",
        return_value="not valid json"
    ):
        response = app.test_client().post(
            "/api/checklist-items/recommend",
            json={
                "message": "What should I prepare for my trip?"
            }
        )

    assert response.status_code == 502
    assert response.get_json()["error"] == (
        "AI service returned an invalid response"
    )
