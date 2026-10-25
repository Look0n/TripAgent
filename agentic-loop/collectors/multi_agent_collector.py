import json
import os
import sqlite3
import time
from contextlib import closing
from hashlib import sha256
from pathlib import Path

from core.validation import ROOT, check, finish


def collect_multi_agent_context(feature, workflow_id=None, database=None):
    started = time.monotonic()
    path = Path(database or os.getenv("MULTI_AGENT_DB_PATH") or ROOT / "shared/multi-agent-server/workflow_state.sqlite3").resolve()
    evidence = {"checks": [], "source": "read-only-workflow-db", "workflow_id": workflow_id, "limitations": [
        "Stored records are reviewed; this does not rerun agents or prove model accuracy.",
        "The coordinator does not persist the original full context snapshot; only worker evidence is available.",
        "A workflow decision is not human approval of this agentic-loop report.",
    ]}
    if not path.is_file():
        check(evidence, "workflow_database", False, "Provide the server's SQLite database or a consistent backup", status="SKIP")
        return finish(evidence, started)
    try:
        # Never import the coordinator: importing it creates/initialises its database.
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)) as connection:
            connection.row_factory = sqlite3.Row
            connection.execute("BEGIN")
            if workflow_id is None:
                latest = connection.execute("SELECT id FROM workflows WHERE feature=? ORDER BY created_at DESC, id DESC LIMIT 1", (feature,)).fetchone()
                workflow_id = latest["id"] if latest else None
                evidence["workflow_id"] = workflow_id
                evidence["selection"] = "Latest workflow by creation time for this feature"
            row = connection.execute("SELECT feature, status, payload FROM workflows WHERE id=?", (workflow_id,)).fetchone()
            if row is None:
                check(evidence, "workflow_found", False, "Workflow ID is absent", status="SKIP")
                return finish(evidence, started)
            if row["feature"] != feature:
                check(evidence, "workflow_feature", False, "Workflow belongs to a different feature")
                return finish(evidence, started)
            if len(row["payload"]) > 200000:
                raise ValueError("Oversized payload")
            payload = json.loads(row["payload"])
            audit = connection.execute("SELECT event, timestamp, detail FROM audit WHERE workflow_id=? ORDER BY id LIMIT 101", (workflow_id,)).fetchall()
        if not isinstance(payload, dict) or len(audit) > 100:
            raise ValueError("Invalid workflow record")
        evidence["snapshot_sha256"] = sha256(json.dumps([payload, [dict(item) for item in audit]], sort_keys=True).encode()).hexdigest()
        evidence["workflow"] = payload
        evidence["audit"] = [{"event": item["event"], "timestamp": item["timestamp"]} for item in audit]
        status = payload.get("status")
        check(evidence, "workflow_identity", payload.get("workflow_id") == workflow_id and payload.get("feature") == feature and status == row["status"])
        check(evidence, "workflow_state", status in ("queued", "running", "pending_review", "completed", "rejected"))
        check(evidence, "user_request", isinstance(payload.get("user_request"), str) and bool(payload["user_request"].strip()))
        active = status in ("queued", "running")
        for agent, field in (("planner", "plan"), ("worker", "output"), ("reviewer", "review")):
            result = payload.get(agent + "_result")
            valid = isinstance(result, dict) and result.get("agent") == agent + "_agent" and result.get("status") == "success" and isinstance(result.get(field), str) and bool(result[field].strip())
            check(evidence, agent + "_result", valid, status="SKIP" if active and result is None else None)
        worker = payload.get("worker_result") or {}
        check(evidence, "worker_evidence", isinstance(worker.get("evidence"), list) and bool(worker["evidence"]), "Empty evidence cannot establish factual support", status="SKIP" if not worker.get("evidence") else None)
        events = [item["event"] for item in audit]
        expected = ["workflow_created", "planner_completed", "worker_completed", "awaiting_human_review"]
        if status in ("completed", "rejected"):
            expected.append("human_review_recorded")
        check(evidence, "audit_order", events == expected, status="SKIP" if active and events == expected[:len(events)] else None)
        decision = payload.get("human_decision") or {}
        check(evidence, "human_required", decision.get("required") is True)
        if status in ("completed", "rejected"):
            value = decision.get("decision")
            check(evidence, "human_decision", decision.get("status") == "completed" and value in ("Accept", "Partially Accept", "Reject") and status == ("rejected" if value == "Reject" else "completed") and bool(decision.get("timestamp")))
            check(evidence, "partial_acceptance_comment", value != "Partially Accept" or (isinstance(decision.get("correction"), str) and bool(decision["correction"].strip())))
            last_detail = json.loads(audit[-1]["detail"]) if audit else {}
            check(evidence, "decision_audit", last_detail.get("decision") == value)
        else:
            check(evidence, "human_pending", decision.get("status") == "pending")
            check(evidence, "human_decision_recorded", False, "Awaiting a human decision", status="SKIP")
    except (OSError, sqlite3.Error, ValueError, TypeError, AttributeError, KeyError) as error:
        check(evidence, "workflow_read", False, type(error).__name__ + ": invalid or unreadable workflow evidence")
    return finish(evidence, started)
