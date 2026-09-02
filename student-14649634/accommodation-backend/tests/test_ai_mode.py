from unittest.mock import patch

from app import app


def test_ai_chat_success():

    client = app.test_client()

    fake_requirements = """
    {
        "city": "Cairns",
        "budget": 300,
        "guests": 3,
        "type": null,
        "preferences": [
            "quiet",
            "resort style",
            "family friendly"
        ]
    }
    """

    fake_reply = (
        "1. Pacific Hotel Cairns\n"
        "Reason: Resort-style atmosphere "
        "and suitable for families."
    )

    fake_accommodations = [
        {
            "accommodation_id": 1,
            "accommodation_name":
                "Pacific Hotel Cairns",
            "type": "Hotel",
            "city": "Cairns",
            "price_per_night": 190,
            "guest_capacity": 3,
            "rating": 4.3,
            "description":
                "Tropical resort-style atmosphere "
                "suitable for families."
        }
    ]

    with patch(
        "routes.ai_mode.generate_text",
        side_effect=[
            fake_requirements,
            fake_reply
        ]
    ), patch(
        "routes.ai_mode.search_for_recommendation",
        return_value=fake_accommodations
    ):

        response = client.post(
            "/api/accommodations/chat",
            json={
                "message":
                    "I want a quiet resort style "
                    "place in Cairns for three people."
            }
        )

    assert response.status_code == 200

    data = response.get_json()

    assert data["matches"] == 1
    assert "Pacific Hotel Cairns" in data["reply"]
    assert data["requirements"]["city"] == "Cairns"
    assert data["requirements"]["guests"] == 3
    
    
def test_ai_chat_missing_message():

    client = app.test_client()

    response = client.post(
        "/api/accommodations/chat",
        json={}
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Message is required."
    
    
@patch(
    "routes.ai_mode.generate_text",
    return_value="""
    {
        "city": "Unknown City",
        "budget": null,
        "guests": null,
        "type": null,
        "preferences": []
    }
    """
)
@patch(
    "routes.ai_mode.search_for_recommendation",
    return_value=[]
)
def test_ai_chat_no_matches(
    mock_search,
    mock_generate
):

    client = app.test_client()

    response = client.post(
        "/api/accommodations/chat",
        json={
            "message":
                "Find accommodation "
                "in Unknown City"
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["matches"] == 0