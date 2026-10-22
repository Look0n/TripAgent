"""Tests for the Flight AI-Mode deployment controls.

The Release 2 cloud baseline requires AI-Mode to be disabled by default in
the cloud deployment. These tests verify the runtime mode switch and the
AI_MODE_LOCKED deployment lock without calling Ollama.
"""
import pytest

from app import app
from routes import ai_mode


BASE = "/api/flight/ai"


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_mode(monkeypatch):
    monkeypatch.delenv("AI_MODE_LOCKED", raising=False)
    ai_mode.set_mode_enabled(True)
    yield
    ai_mode.set_mode_enabled(True)


def test_mode_reports_enabled_and_unlocked_locally(client):
    response = client.get(f"{BASE}/mode")

    assert response.status_code == 200
    assert response.get_json() == {"enabled": True, "locked": False}


def test_mode_can_be_disabled_at_runtime(client):
    response = client.put(f"{BASE}/mode", json={"enabled": False})

    assert response.status_code == 200
    assert response.get_json()["enabled"] is False
    assert ai_mode.mode_enabled() is False


def test_mode_rejects_non_boolean(client):
    response = client.put(f"{BASE}/mode", json={"enabled": "off"})

    assert response.status_code == 400


def test_recommend_refused_when_mode_disabled(client):
    ai_mode.set_mode_enabled(False)

    response = client.post(
        f"{BASE}/recommend",
        json={"message": "cheapest flight to Melbourne"},
    )

    assert response.status_code == 403
    assert "OFF" in response.get_json()["error"]


def test_lock_overrides_runtime_mode(client, monkeypatch):
    monkeypatch.setenv("AI_MODE_LOCKED", "true")
    ai_mode.set_mode_enabled(True)

    mode = client.get(f"{BASE}/mode").get_json()

    assert mode == {"enabled": False, "locked": True}

    response = client.post(
        f"{BASE}/recommend",
        json={"message": "cheapest flight to Melbourne"},
    )

    assert response.status_code == 403
    assert "locked" in response.get_json()["error"]


def test_lock_refuses_runtime_enable(client, monkeypatch):
    monkeypatch.setenv("AI_MODE_LOCKED", "true")

    response = client.put(f"{BASE}/mode", json={"enabled": True})

    assert response.status_code == 403


def test_html_recommend_refused_when_disabled(client):
    ai_mode.set_mode_enabled(False)

    response = client.post(
        f"{BASE}/recommend/html",
        data={"message": "cheapest flight to Melbourne"},
    )

    assert response.status_code == 403
    assert b"disabled" in response.data
