from unittest.mock import Mock

import pytest
import requests

from core.feature_modes import run_with_mode


SERVICE = {"name": "Checklist", "endpoints": {"base_url": "http://localhost:5004"}}


def switch(monkeypatch, enabled=False, locked=False, fail_restore=False):
    state = {"enabled": enabled, "locked": locked}
    calls = []
    def request(method, url, **kwargs):
        calls.append((method, kwargs.get("json")))
        if method != "GET":
            state["enabled"] = kwargs["json"]["enabled"]
            if fail_restore and not state["enabled"]:
                raise requests.Timeout()
        response = Mock()
        response.json.return_value = dict(state)
        return response
    monkeypatch.setattr("core.feature_modes.requests.request", request)
    return state, calls


@pytest.mark.parametrize("mode", ["mcp", "rag", "multi-agent"])
def test_off_is_enabled_during_pipeline_and_restored(monkeypatch, mode):
    state, calls = switch(monkeypatch)
    def pipeline():
        assert state["enabled"]
        return {"validation_status": "PASS"}
    result = run_with_mode(SERVICE, "checklist", mode, pipeline)
    assert result["feature_mode"]["restored"] is True
    assert state["enabled"] is False
    assert [data for verb, data in calls if verb == "POST"] == [{"enabled": True}, {"enabled": False}]


def test_original_on_stays_on(monkeypatch):
    state, calls = switch(monkeypatch, enabled=True)
    run_with_mode(SERVICE, "checklist", "mcp", lambda: {})
    assert state["enabled"]
    assert all(method == "GET" for method, _ in calls)


@pytest.mark.parametrize("error", [RuntimeError, KeyboardInterrupt])
def test_exception_restores_switch(monkeypatch, error):
    state, _ = switch(monkeypatch)
    def pipeline():
        raise error()
    with pytest.raises(error):
        run_with_mode(SERVICE, "checklist", "mcp", pipeline)
    assert not state["enabled"]


def test_locked_mode_is_not_changed(monkeypatch):
    _, calls = switch(monkeypatch, locked=True)
    pipeline = Mock()
    result = run_with_mode(SERVICE, "checklist", "mcp", pipeline)
    assert result["execution_status"] == "MODE_FAILED"
    pipeline.assert_not_called()
    assert calls == [("GET", None)]


def test_restore_failure_cannot_pass(monkeypatch):
    switch(monkeypatch, fail_restore=True)
    result = run_with_mode(SERVICE, "checklist", "rag", lambda: {"validation_status": "PASS"})
    assert result["execution_status"] == "MODE_RESTORE_FAILED"
    assert result["validation_status"] == "FAIL"


def test_backend_unavailable_blocks_pipeline(monkeypatch):
    monkeypatch.setattr("core.feature_modes.requests.request", Mock(side_effect=requests.ConnectionError()))
    pipeline = Mock()
    assert run_with_mode(SERVICE, "checklist", "mcp", pipeline)["execution_status"] == "MODE_FAILED"
    pipeline.assert_not_called()
