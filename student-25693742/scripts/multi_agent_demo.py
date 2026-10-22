"""Terminal demo of the Attractions Multi-Agent workflow (Release 2).

Runs Planner -> Worker -> Reviewer -> Human Review through the Attractions
backend/API, which forwards to the shared non-containerised Multi-Agent Server.

Usage:
    python multi_agent_demo.py --request "A cultural tour in Sydney under $60" \
        --city Sydney --max-price 60 --decision Accept
"""

import argparse
import json
import sys
import time
from datetime import datetime

import requests


def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def show(title, data):
    log(title)
    print(json.dumps(data, indent=2, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="http://localhost:5003")
    parser.add_argument("--request", required=True)
    parser.add_argument("--city", default="")
    parser.add_argument("--category", default="")
    parser.add_argument("--max-price", default="")
    parser.add_argument(
        "--decision",
        default="Accept",
        choices=["Accept", "Partially Accept", "Reject"],
    )
    parser.add_argument("--correction", default="")
    args = parser.parse_args()

    api = f"{args.backend}/api/attractions/multi-agent"

    show("Multi-Agent Server health (via attractions backend)",
         requests.get(f"{api}/health", timeout=15).json())

    show("Enable Multi-Agent Mode",
         requests.put(f"{api}/mode", json={"enabled": True}, timeout=15).json())

    response = requests.post(f"{api}/workflow", json={
        "user_request": args.request,
        "city": args.city,
        "category": args.category,
        "max_price": args.max_price,
    }, timeout=30)

    created = response.json()

    if response.status_code != 202:
        show(f"Workflow refused (HTTP {response.status_code})", created)
        return 1

    workflow_id = created["workflow_id"]
    log(f"Workflow {workflow_id} created with {len(created['evidence'])} "
        "attraction records as evidence")
    show("Evidence supplied to the agents", created["evidence"])

    seen = set()
    started = time.monotonic()

    while True:
        workflow = requests.get(f"{api}/workflow/{workflow_id}", timeout=15).json()

        for key, label in (
            ("planner_result", "PLANNER"),
            ("worker_result", "WORKER"),
            ("reviewer_result", "REVIEWER"),
        ):
            if workflow.get(key) and key not in seen:
                seen.add(key)
                show(f"{label} completed ({int(time.monotonic() - started)}s)",
                     workflow[key])

        if workflow["status"] not in ("queued", "running"):
            break

        time.sleep(2)

    log(f"Workflow status: {workflow['status']}")

    if workflow["status"] != "pending_review":
        show("Workflow did not reach human review", workflow)
        return 1

    show(f"HUMAN REVIEW decision submitted: {args.decision}",
         {"decision": args.decision, "correction": args.correction})

    reviewed = requests.post(f"{api}/workflow/{workflow_id}/review", json={
        "decision": args.decision,
        "correction": args.correction,
    }, timeout=15).json()

    show("Final workflow record", reviewed)

    show("Attractions workflow history",
         requests.get(f"{api}/history", timeout=15).json())

    return 0


if __name__ == "__main__":
    sys.exit(main())
