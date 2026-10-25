import json
from datetime import datetime, timezone
import requests
from services import database_api

EVIDENCE_FIELDS = ("item_id", "title", "item_type", "category", "description", "priority", "is_completed")

MAX_CONTEXT_LENGTH = 12000

class ChecklistContextError(RuntimeError):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code

def build_checklist_context():
    try:
        response = database_api.get_checklist_items()
        response.raise_for_status()

    except requests.RequestException as exc:
        raise ChecklistContextError("Checklist database service is unavailable") from exc

    try:
        items = response.json()

    except ValueError as exc:
        raise ChecklistContextError("Checklist database returned invalid JSON", 502, ) from exc

    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ChecklistContextError("Checklist database returned an invalid item list", 502, )

    evidence = []

    for item in items:
        if(type(item.get("item_id")) is not int or not isinstance(item.get("title"), str) or item.get("is_completed") not in (0, 1, False, True)):
            raise ChecklistContextError("Checklist database returned an invalid item", 502, )

        record = {field: item.get(field) for field in EVIDENCE_FIELDS}

        record["is_completed"] = bool(record["is_completed"])

        evidence.append(record)

    completed = sum(item["is_completed"] for item in evidence)

    high_priority_pending = sum(item["priority"] == "High" and not item["is_completed"] for item in evidence)

    context = {
        "feature": "checklist",
        "task": "pre_trip_checklist_review",
        "source": "checklist_database /checklist-items",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(evidence),
            "completed": completed,
            "pending": len(evidence) - completed,
            "high_priority_pending": high_priority_pending,
        },
        "evidence": evidence,
        "constraints": {
            "read_only": True,
            "human_review_required": True,
            "max_suggestions": 5,
        }
    }

    if len(json.dumps(context)) > MAX_CONTEXT_LENGTH:
        raise ChecklistContextError("Checklist evidence is too large for one workflow", 413)

    return context