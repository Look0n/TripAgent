from unittest.mock import Mock

import pytest
import requests
from collectors import rag_collector as collector


ROWS = [{"chunk_id": "checklist_knowledge_priority", "source_id": "rag-knowledge:checklist", "authority_tier": "tier_2", "text": "High Medium Low"}]
CASE = {"answerable": True, "relevant_ids": ["checklist_knowledge_priority"]}


def answer():
    return {"status": "success", "feature": "checklist", "answer": "High, Medium or Low.", "citations": [{k: ROWS[0][k] for k in ("chunk_id", "source_id", "authority_tier")}], "confidence_category": "Medium", "insufficient_context": False}


def test_metrics_use_unique_reference_ids():
    metrics = collector.retrieval_metrics(ROWS + ROWS, CASE["relevant_ids"])
    assert metrics["p_at_5"] == 0.2
    assert metrics["r_at_5"] == 1
    assert collector.retrieval_metrics([], [])["r_at_5"] is None


def test_grounded_contract():
    assert collector.validate_answer(answer(), ROWS, CASE)


@pytest.mark.parametrize("change", [{"citations": []}, {"citations": [{"chunk_id": "invented"}]}, {"confidence_category": "certain"}, {"answer": "Ollama unavailable: connection failed"}, {"insufficient_context": True}])
def test_invalid_answer_rejected(change):
    data = answer()
    data.update(change)
    assert not collector.validate_answer(data, ROWS, CASE)


def test_insufficient_context_contract():
    data = {"status": "success", "answer": "Insufficient context.", "citations": [], "confidence_category": "Unknown", "insufficient_context": True}
    assert collector.validate_answer(data, [], {"answerable": False})
    data["citations"] = answer()["citations"]
    assert not collector.validate_answer(data, ROWS, {"answerable": False})


def test_live_timeout_fails_setup(monkeypatch):
    monkeypatch.setattr(collector.requests, "get", Mock(side_effect=requests.Timeout()))
    passed, evidence = collector.collect_rag_context("checklist", {})
    assert not passed
    assert evidence["validation_status"] == "FAIL"
    assert evidence["checks"][-1]["id"] == "rag_setup"


def test_full_rag_flow(monkeypatch):
    case = {"id": "priority", "query": "Priorities?", **CASE}
    monkeypatch.setattr(collector, "rag_cases", lambda feature: [case])
    monkeypatch.setattr(collector.requests, "get", Mock(return_value=Mock(json=lambda: {"status": "healthy"})))
    calls = []
    def post(path, payload):
        calls.append(path)
        return {"chunk_count": 1} if path.endswith("refresh") else {"results": ROWS, "feature": "checklist"} if path.endswith("retrieve") else answer()
    monkeypatch.setattr(collector, "post", post)
    passed, evidence = collector.collect_rag_context("checklist", {})
    assert passed
    assert calls == ["/rag/refresh", "/rag/retrieve", "/rag/answer"]
    assert evidence["queries"][0]["metrics"]["r_at_5"] == 1
