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


def test_recommend_requires_message(client):
    response = client.post("/api/attractions/recommend", json={})

    assert response.status_code == 400
