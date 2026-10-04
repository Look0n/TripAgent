import json
from pathlib import Path

from core import reporter, orchestrator
from core.validation import sanitise


def test_redaction():
    value = sanitise({"profile": {"email": "test@example.com"}, "nested": [{"authorization": "Bearer secret"}], "text": "test@example.com"})
    assert "secret" not in json.dumps(value)
    assert "test@example.com" not in json.dumps(value)


def test_unique_reports_and_metadata(tmp_path, monkeypatch):
    fake_file = tmp_path / "agentic-loop" / "core" / "reporter.py"
    monkeypatch.setattr(reporter, "__file__", str(fake_file))
    monkeypatch.setattr(reporter, "repository_state", lambda: {"commit": "fixture", "dirty": True})
    data = {"checklist": {"execution_status": "COMPLETED", "validation_status": "FAIL", "model_status": "NOT_RUN", "evidence": {"checks": [], "password": "secret"}}}
    first = reporter.save_run_report(data, "mcp")
    second = reporter.save_run_report(data, "mcp")
    assert first != second and first.exists() and second.exists()
    assert first.with_suffix(".md").exists()
    assert "secret" not in first.read_text()
    assert json.loads(first.read_text())["repository"]["commit"] == "fixture"


def test_cli_failed_validation_exit(monkeypatch):
    monkeypatch.setattr("sys.argv", ["loop", "--mode", "mcp", "--service", "checklist", "--checks-only"])
    monkeypatch.setattr(orchestrator, "run_mcp_pipeline", lambda *args, **kwargs: {"execution_status": "COMPLETED", "validation_status": "FAIL"})
    monkeypatch.setattr(orchestrator, "save_run_report", lambda *args, **kwargs: None)
    assert orchestrator.main() == 1


def test_old_db_mode_dispatch_preserved(monkeypatch):
    monkeypatch.setattr("sys.argv", ["loop", "--mode", "db", "--service", "checklist"])
    monkeypatch.setattr(orchestrator, "run_db_pipeline", lambda *args: {"status": "COMPLETED"})
    monkeypatch.setattr(orchestrator, "save_run_report", lambda *args, **kwargs: None)
    assert orchestrator.main() == 0


def test_default_all_saves_every_mode(monkeypatch):
    monkeypatch.setattr("sys.argv", ["loop", "--service", "checklist"])
    monkeypatch.setattr(orchestrator, "collect_project_context", lambda: {})
    result = {"status": "COMPLETED", "execution_status": "COMPLETED", "validation_status": "PASS", "model_status": "COMPLETED", "output_checks": {"format": True}}
    outputs = {}
    for name in ("db", "endpoints", "architecture", "devops", "mcp", "rag"):
        outputs[name] = {**result, "marker": name}
        monkeypatch.setattr(orchestrator, f"run_{name}_pipeline", lambda *args, value=outputs[name], **kwargs: value)
    saved = {}
    combined = []
    monkeypatch.setattr(orchestrator, "save_run_report", lambda data, mode: saved.update({mode: data}))
    monkeypatch.setattr(orchestrator, "save_report", combined.append)
    assert orchestrator.main() == 0
    assert set(saved) == set(outputs)
    for mode, data in saved.items():
        assert data["checklist"] == outputs[mode]
    assert len(combined) == 1
    assert combined[0]["checklist"]["database_analysis"] == outputs["db"]
