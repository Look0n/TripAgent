import json
import sqlite3

import pytest

from collectors.multi_agent_collector import collect_multi_agent_context
from collectors.testing_collector import collect_testing_context
from config.services import SERVICES
from core import orchestrator, reporter
from pipelines import evidence_pipeline
from pipelines.multi_agent_pipeline import run_multi_agent_pipeline
from pipelines.testing_pipeline import run_testing_pipeline


SHA = "a" * 40
CONFIG = SERVICES["checklist"]


def workflow_db(tmp_path, decision="Accept", status="completed", correction="", reverse=False):
    path = tmp_path / "workflow.sqlite3"
    payload = {"workflow_id": "example", "feature": "checklist", "status": status, "user_request": "Review packing", "human_decision": {"required": True, "status": "completed", "decision": decision, "correction": correction, "timestamp": "2026-10-25T00:00:00Z"}}
    for agent, field in (("planner", "plan"), ("worker", "output"), ("reviewer", "review")):
        payload[agent + "_result"] = {"agent": agent + "_agent", "status": "success", field: "Recorded output"}
    payload["worker_result"]["evidence"] = [{"item_id": 1, "title": "Passport"}]
    events = ["workflow_created", "planner_completed", "worker_completed", "awaiting_human_review", "human_review_recorded"]
    if status == "pending_review":
        events.pop()
        payload["human_decision"] = {"required": True, "status": "pending"}
    if reverse:
        events[1], events[2] = events[2], events[1]
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE workflows(id TEXT, feature TEXT, status TEXT, payload TEXT)")
        connection.execute("CREATE TABLE audit(id INTEGER PRIMARY KEY, workflow_id TEXT, event TEXT, timestamp TEXT, detail TEXT)")
        connection.execute("INSERT INTO workflows VALUES (?, ?, ?, ?)", ("example", "checklist", status, json.dumps(payload)))
        for event in events:
            connection.execute("INSERT INTO audit(workflow_id, event, timestamp, detail) VALUES (?, ?, ?, ?)", ("example", event, "2026-10-25T00:00:00Z", json.dumps({"decision": decision} if event == "human_review_recorded" else {})))
    return path


@pytest.mark.parametrize("decision,status,correction", [("Accept", "completed", ""), ("Reject", "rejected", ""), ("Partially Accept", "completed", "Recheck passport")])
def test_valid_workflow_is_read_only(tmp_path, decision, status, correction):
    path = workflow_db(tmp_path, decision, status, correction)
    before = path.read_bytes()
    passed, evidence = collect_multi_agent_context("checklist", "example", path)
    assert passed and evidence["validation_status"] == "PASS"
    assert path.read_bytes() == before


@pytest.mark.parametrize("kwargs", [{"reverse": True}, {"decision": "Partially Accept"}, {"decision": "Reject"}, {"status": "failed"}])
def test_invalid_workflow_fails(tmp_path, kwargs):
    path = workflow_db(tmp_path, **kwargs)
    assert collect_multi_agent_context("checklist", "example", path)[1]["validation_status"] == "FAIL"


def test_pending_workflow_and_missing_database_are_partial(tmp_path):
    path = workflow_db(tmp_path, status="pending_review")
    assert collect_multi_agent_context("checklist", "example", path)[1]["validation_status"] == "PARTIAL"
    missing = tmp_path / "missing.sqlite3"
    assert collect_multi_agent_context("checklist", "example", missing)[1]["validation_status"] == "PARTIAL"
    assert not missing.exists()


def test_wrong_feature_is_not_disclosed(tmp_path):
    path = workflow_db(tmp_path)
    _, evidence = collect_multi_agent_context("account", "example", path)
    assert evidence["validation_status"] == "FAIL"
    assert "workflow" not in evidence


def test_automatic_workflow_selection_is_feature_scoped(tmp_path):
    path = workflow_db(tmp_path)
    with sqlite3.connect(path) as connection:
        connection.execute("ALTER TABLE workflows ADD COLUMN created_at TEXT")
        connection.execute("UPDATE workflows SET created_at='2026-10-24'")
        payload = json.loads(connection.execute("SELECT payload FROM workflows").fetchone()[0])
        payload["workflow_id"] = "newest"
        connection.execute("INSERT INTO workflows VALUES (?, ?, ?, ?, ?)", ("newest", "checklist", "completed", json.dumps(payload), "2026-10-25"))
        connection.execute("INSERT INTO workflows VALUES (?, ?, ?, ?, ?)", ("other-feature", "flight", "completed", "{}", "2026-10-26"))
    _, evidence = collect_multi_agent_context("checklist", database=path)
    assert evidence["workflow_id"] == "newest"
    assert evidence["workflow"]["feature"] == "checklist"


def make_manifest(tmp_path):
    (tmp_path / "pre-commit.log").write_text("ruff.....................................................................Passed\nDetect secrets...........................................................Passed\npip-audit................................................................Passed\n", encoding="utf-8")
    (tmp_path / "tests.xml").write_text('<testsuites><testsuite tests="2" failures="0" errors="0"><testcase classname="tests.routes" name="test_start"/><testcase classname="tests.routes" name="test_review"/></testsuite></testsuites>', encoding="utf-8")
    manifest = {"feature": "checklist", "commit": SHA, "pre_commit": {"commit": SHA, "log": "pre-commit.log", "exit_code": 0}, "ci": {"commit": SHA, "workflow": CONFIG["ci_pipeline"], "run_url": "https://github.com/Look0n/TripAgent/actions/runs/123", "conclusion": "success", "junit": ["tests.xml"], "endpoints": [
        {"method": "POST", "path": "/api/checklist-items/multi-agent/workflow", "tests": ["tests.routes::test_start"]},
        {"method": "POST", "path": "/api/checklist-items/multi-agent/workflow/<uuid>/review", "tests": ["tests.routes::test_review"]},
    ]}}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path, manifest


def test_testing_reports_pass(tmp_path):
    path, _ = make_manifest(tmp_path)
    passed, evidence = collect_testing_context("checklist", CONFIG, path, SHA)
    assert passed and evidence["test_summary"] == {"PASS": 2, "FAIL": 0, "SKIP": 0}
    assert len(evidence["artifacts"]) == 3


@pytest.mark.parametrize("change", ["wrong_commit", "wrong_feature", "wrong_workflow", "one_endpoint", "unknown_test", "failed_ci", "outside_path"])
def test_invalid_make_manifest(tmp_path, change):
    path, manifest = make_manifest(tmp_path)
    if change == "wrong_commit":
        manifest["commit"] = "b" * 40
    elif change == "wrong_feature":
        manifest["feature"] = "flight"
    elif change == "wrong_workflow":
        manifest["ci"]["workflow"] = "other.yml"
    elif change == "one_endpoint":
        manifest["ci"]["endpoints"].pop()
    elif change == "unknown_test":
        manifest["ci"]["endpoints"][0]["tests"] = ["does_not_exist"]
    elif change == "failed_ci":
        manifest["ci"]["conclusion"] = "failure"
    else:
        manifest["pre_commit"]["log"] = "../outside.log"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert collect_testing_context("checklist", CONFIG, path, SHA)[1]["validation_status"] == "FAIL"


@pytest.mark.parametrize("xml", ['<testsuite><testcase name="x"><failure/></testcase></testsuite>', '<testsuite><error/></testsuite>', '<!DOCTYPE x [<!ENTITY y "z">]><testsuite/>', 'not xml'])
def test_failed_or_malformed_junit(tmp_path, xml):
    path, _ = make_manifest(tmp_path)
    (tmp_path / "tests.xml").write_text(xml, encoding="utf-8")
    assert collect_testing_context("checklist", CONFIG, path, SHA)[1]["validation_status"] == "FAIL"


def test_skipped_tests_do_not_pass(tmp_path):
    path, _ = make_manifest(tmp_path)
    xml_path = tmp_path / "tests.xml"
    xml_path.write_text(xml_path.read_text().replace('name="test_start"/>', 'name="test_start"><skipped/></testcase>'))
    assert not collect_testing_context("checklist", CONFIG, path, SHA)[0]


@pytest.mark.parametrize("status,expected", [("Skipped", "PARTIAL"), ("Failed", "FAIL")])
def test_pre_commit_does_not_hide_failure_or_skip(tmp_path, status, expected):
    path, _ = make_manifest(tmp_path)
    log = tmp_path / "pre-commit.log"
    log.write_text(log.read_text().replace("Passed", status))
    assert collect_testing_context("checklist", CONFIG, path, SHA)[1]["validation_status"] == expected


def test_missing_reports_are_partial(tmp_path):
    path, _ = make_manifest(tmp_path)
    (tmp_path / "pre-commit.log").unlink()
    assert collect_testing_context("checklist", CONFIG, path, SHA)[1]["validation_status"] == "PARTIAL"
    assert collect_testing_context("checklist", CONFIG, tmp_path / "absent.json", SHA)[1]["validation_status"] == "PARTIAL"
    (tmp_path / "tests.xml").unlink()
    assert collect_testing_context("checklist", CONFIG, path, SHA)[1]["validation_status"] == "PARTIAL"


@pytest.mark.parametrize("attribute,expected", [('tests="99"', "FAIL"), ('tests="2" skipped="1"', "PARTIAL")])
def test_junit_summary_cannot_hide_missing_or_skipped_tests(tmp_path, attribute, expected):
    path, _ = make_manifest(tmp_path)
    xml = tmp_path / "tests.xml"
    xml.write_text(xml.read_text().replace('tests="2"', attribute))
    assert collect_testing_context("checklist", CONFIG, path, SHA)[1]["validation_status"] == expected


def test_checks_only_never_calls_models(tmp_path, monkeypatch):
    def unexpected(*args):
        pytest.fail("Model must not run")
    monkeypatch.setattr(evidence_pipeline, "run_implementation", unexpected)
    path = workflow_db(tmp_path)
    assert reporter.validation_passed(run_multi_agent_pipeline(CONFIG, "checklist", "example", path, checks_only=True), True)
    manifest, _ = make_manifest(tmp_path)
    assert reporter.validation_passed(run_testing_pipeline(CONFIG, "checklist", manifest, SHA, checks_only=True), True)


def test_models_cannot_override_failed_validation(tmp_path, monkeypatch):
    path = workflow_db(tmp_path, reverse=True)
    monkeypatch.setattr(evidence_pipeline, "run_implementation", lambda *args: "Everything passed")
    monkeypatch.setattr(evidence_pipeline, "run_review", lambda *args: "Strengths: fine Risk: none Correction: none Retest: none")
    result = run_multi_agent_pipeline(CONFIG, "checklist", "example", path)
    assert result["model_status"] == "COMPLETED"
    assert not reporter.validation_passed(result)


def test_model_failure_is_recorded(tmp_path, monkeypatch):
    def fail(*args):
        raise RuntimeError("secret detail")
    path = workflow_db(tmp_path)
    monkeypatch.setattr(evidence_pipeline, "run_implementation", fail)
    result = run_multi_agent_pipeline(CONFIG, "checklist", "example", path)
    assert result["execution_status"] == "IMPLEMENTATION_FAILED"
    assert "secret detail" not in json.dumps(result)


@pytest.mark.parametrize("mode,argument", [("multi-agent", ["--workflow-id", "example"]), ("testing", ["--evidence", "manifest.json"])])
def test_new_cli_dispatch_and_reports(monkeypatch, tmp_path, mode, argument):
    monkeypatch.setattr("sys.argv", ["loop", "--mode", mode, "--service", "checklist", "--checks-only", *argument])
    result = {"execution_status": "COMPLETED", "validation_status": "PASS", "model_status": "NOT_RUN"}
    monkeypatch.setattr(orchestrator, "run_" + mode.replace("-", "_") + "_pipeline", lambda *args, **kwargs: result)
    monkeypatch.setattr(reporter, "__file__", str(tmp_path / "agentic-loop/core/reporter.py"))
    monkeypatch.setattr(reporter, "repository_state", lambda: {"commit": SHA, "dirty": False})
    assert orchestrator.main() == 0
    reports = list(tmp_path.glob("docs/evidence/agentic-loop/runs/*.json"))
    assert len(reports) == 1
    assert reports[0].with_suffix(".md").exists()
    assert json.loads(reports[0].read_text())["source"] != "live-services"


@pytest.fixture(autouse=True)
def isolate_cli_mode_switches(monkeypatch):
    monkeypatch.setattr(orchestrator, "run_with_mode", lambda service, feature, mode, pipeline: pipeline())
