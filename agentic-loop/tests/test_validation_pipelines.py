from unittest.mock import Mock

import pytest
from pipelines import mcp_pipeline, rag_pipeline
from core.reporter import validation_passed


@pytest.mark.parametrize("module,mode", [(mcp_pipeline,"mcp"), (rag_pipeline,"rag")])
def test_review_cannot_override_failed_checks(monkeypatch, module, mode):
    monkeypatch.setattr(module, f"collect_{mode}_context", lambda *args: (False, {"validation_status": "FAIL", "checks": []}))
    monkeypatch.setattr(module, "run_implementation", Mock(return_value="Looks good"))
    monkeypatch.setattr(module, "run_review", Mock(return_value="Strengths: All good Risk: None Correction: None Retest: None"))
    output = getattr(module, f"run_{mode}_pipeline")({"name": "Checklist"}, "checklist")
    assert output["model_status"] == "COMPLETED"
    assert not validation_passed(output)
    if mode == "rag":
        assert "vector-store" in output["review_prompt"]
        assert "Looks good" in output["review_prompt"]


def test_checks_only_never_calls_models(monkeypatch):
    monkeypatch.setattr(mcp_pipeline, "collect_mcp_context", lambda *args: (True, {"validation_status": "PASS"}))
    implementation = Mock(side_effect=AssertionError("Should not run"))
    monkeypatch.setattr(mcp_pipeline, "run_implementation", implementation)
    output = mcp_pipeline.run_mcp_pipeline({"name": "Checklist"}, "checklist", True)
    implementation.assert_not_called()
    assert validation_passed(output, True)
    assert not validation_passed(output)


def test_review_failure_is_not_success(monkeypatch):
    monkeypatch.setattr(rag_pipeline, "collect_rag_context", lambda *args: (True, {"validation_status": "PASS"}))
    monkeypatch.setattr(rag_pipeline, "run_implementation", Mock(return_value="Evidence evaluated"))
    monkeypatch.setattr(rag_pipeline, "run_review", Mock(side_effect=RuntimeError("Offline")))
    output = rag_pipeline.run_rag_pipeline({"name": "Checklist"}, "checklist")
    assert output["execution_status"] == "REVIEW_FAILED"
    assert not validation_passed(output)
