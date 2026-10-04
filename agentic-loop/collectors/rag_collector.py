import ast
import time

import requests

from config.review_config import RAG_SERVICE_URL, RAG_TIMEOUT_SECONDS
from config.validation_cases import rag_cases
from core.validation import ROOT, check, finish, sanitise, structure


def retrieval_metrics(rows, relevant_ids):
    ids = [row["chunk_id"] for row in rows[:5]]
    relevant = set(relevant_ids)
    hits = set(ids) & relevant
    return {"retrieved_ids": ids, "reference_ids": sorted(relevant), "relevant_retrieved_ids": sorted(hits), "p_at_5": len(hits) / 5 if relevant else None, "r_at_5": len(hits) / len(relevant) if relevant else None, "scope": "Curated feature-knowledge reference set; not exhaustive relevance labels for the full corpus"}


def validate_answer(answer, rows, case):
    if not isinstance(answer, dict) or answer.get("status") != "success":
        return False
    text = answer.get("answer")
    citations = answer.get("citations")
    confidence = str(answer.get("confidence_category", "")).lower()
    if not isinstance(text, str) or not text.strip() or not isinstance(citations, list):
        return False
    if confidence not in {"high", "medium", "low", "unknown"} or "ollama unavailable" in text.lower():
        return False
    if not case["answerable"]:
        return answer.get("insufficient_context") is True and not citations and confidence == "unknown"
    if answer.get("insufficient_context") is True or not citations:
        return False
    sources = {(row["chunk_id"], row["source_id"], row["authority_tier"]) for row in rows}
    return all(isinstance(c, dict) and (c.get("chunk_id"), c.get("source_id"), c.get("authority_tier")) in sources for c in citations)


def post(path, payload):
    response = requests.post(RAG_SERVICE_URL + path, json=payload, timeout=(5, RAG_TIMEOUT_SECONDS))
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or data.get("status") != "success":
        raise ValueError("RAG returned an unsuccessful or invalid JSON object")
    return data


def collect_rag_context(feature, service):
    started = time.monotonic()
    evidence = {"feature": feature, "server": RAG_SERVICE_URL, "checks": [], "queries": [], "limitations": ["Corpus refresh updates the local index and audit log", "Citation membership is not proof that all answer claims are supported", "Human review of answer grounding and confidence remains required", "Retrieval metrics use a curated reference subset, with no rubric-defined numeric threshold"]}
    structure(evidence, ["shared/rag-server/rag_pipeline.py", "shared/rag-server/rag_http_server.py", "shared/rag-server/requirements.txt", "prompts/service/implementation/rag_implementation_prompt.txt", "prompts/service/review/rag_review_prompt.txt", "prompts/service/review/rag_reasoning_prompt.txt"])
    try:
        code = (ROOT / "shared/rag-server/rag_pipeline.py").read_text(encoding="utf-8-sig")
        tree = ast.parse(code)
        functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        check(evidence, "rag_functions", {"refresh_corpus", "retrieve_context", "answer_question"} <= functions)
        names = {"chunk_text", "embed_text", "confidence_from_results"}
        evidence["implementation_context"] = {node.name: ast.get_source_segment(code, node) for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names}
        response = requests.get(RAG_SERVICE_URL + "/health", timeout=5)
        response.raise_for_status()
        healthy = response.json().get("status") == "healthy"
        check(evidence, "health", healthy)
        if not healthy:
            return finish(evidence, started)
        refreshed = post("/rag/refresh", {"feature": feature, "caller": "agentic-loop"})
        evidence["refresh"] = sanitise(refreshed)
        check(evidence, "refresh", type(refreshed.get("chunk_count")) is int and refreshed["chunk_count"] > 0)
    except (OSError, ValueError, requests.RequestException) as exc:
        check(evidence, "rag_setup", False, {"error_type": type(exc).__name__})
        return finish(evidence, started)
    for case in rag_cases(feature):
        query_started = time.monotonic()
        result = {"case": case}
        try:
            payload = {"feature": feature, "query": case["query"], "k": 5, "caller": "agentic-loop"}
            retrieval = post("/rag/retrieve", payload)
            check(evidence, case["id"] + ":feature", retrieval.get("feature") == feature)
            rows = retrieval.get("results")
            valid = isinstance(rows, list) and all(isinstance(row, dict) and all(isinstance(row.get(key), str) and row[key].strip() for key in ("chunk_id", "source_id", "authority_tier", "text")) for row in rows)
            if valid:
                valid = len({row["chunk_id"] for row in rows}) == len(rows) and all(row["authority_tier"] in {"tier_1", "tier_2", "tier_3"} for row in rows)
            check(evidence, case["id"] + ":retrieval_contract", valid)
            if not valid:
                raise ValueError("Invalid retrieval result contract")
            result["retrieval"] = sanitise(retrieval)
            result["metrics"] = retrieval_metrics(rows, case["relevant_ids"])
            if case["answerable"]:
                check(evidence, case["id"] + ":reference_hit", bool(result["metrics"]["relevant_retrieved_ids"]), result["metrics"])
            answer = post("/rag/answer", payload)
            check(evidence, case["id"] + ":answer_feature", answer.get("feature") == feature)
            result["answer"] = sanitise(answer)
            check(evidence, case["id"] + ":answer_contract", validate_answer(answer, rows, case))
        except (ValueError, requests.RequestException) as exc:
            check(evidence, case["id"] + ":execution", False, {"error_type": type(exc).__name__})
        result["duration_seconds"] = round(time.monotonic() - query_started, 3)
        evidence["queries"].append(result)
    return finish(evidence, started)
