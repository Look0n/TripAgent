import os
import requests


MULTI_AGENT_SERVICE_URL =  os.getenv("MULTI_AGENT_SERVICE_URL", "http://host.docker.internal:7003").rstrip("/")

MULTI_AGENT_TIMEOUT_SECONDS = float(os.getenv("MULTI_AGENT_TIMEOUT_SECONDS", "300"))


def check_multi_agent_health():
    response = requests.get(
        f"{MULTI_AGENT_SERVICE_URL}/health",
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def run_multi_agent_workflow(
    feature,
    user_request,
    evidence=None
):
    payload = {
        "feature": feature,
        "user_request": user_request,
        "context": {
            "evidence": evidence or []
        }
    }

    response = requests.post(
        f"{MULTI_AGENT_SERVICE_URL}/workflow",
        json=payload,
        timeout=MULTI_AGENT_TIMEOUT_SECONDS
    )

    response.raise_for_status()
    return response.json()


def submit_human_review(
    workflow_id,
    decision,
    feature="accommodation",
    correction=""
):
    payload = {
        "feature": feature,
        "decision": decision,
        "correction": correction
    }

    response = requests.post(
        f"{MULTI_AGENT_SERVICE_URL}/workflow/{workflow_id}/review",
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    return response.json()


def get_workflow(workflow_id, feature="accommodation"):
    response = requests.get(
        f"{MULTI_AGENT_SERVICE_URL}/workflow/{workflow_id}",
        params={"feature": feature},
        timeout=30
    )

    response.raise_for_status()
    return response.json()