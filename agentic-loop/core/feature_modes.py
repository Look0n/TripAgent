import os

import requests


PREFIXES = {"account": "account", "accommodation": "accommodations", "attractions": "attractions", "checklist": "checklist-items", "flight": "flight"}


def run_with_mode(service, feature, mode, pipeline):
    """Temporarily enable an existing backend switch, then restore its state."""
    result = None
    restore = False
    state = {"mode": mode, "restored": None}
    headers = {}
    if feature == "account" and os.getenv("LOOP_ACCOUNT_CUSTOMER_ID"):
        headers["X-Customer-ID"] = os.environ["LOOP_ACCOUNT_CUSTOMER_ID"]
    url = service["endpoints"]["base_url"].rstrip("/") + f"/api/{PREFIXES[feature]}/{mode}/mode"
    method = "POST" if feature in ("checklist", "accommodation") else "PUT"
    def request(verb, **kwargs):
        response = requests.request(verb, url, headers=headers, timeout=10, **kwargs)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or type(data.get("enabled")) is not bool:
            raise ValueError("Invalid mode response")
        return data
    try:
        # These features use environment flags, not mutable MCP/RAG endpoints.
        if feature in ("accommodation", "attractions") and mode in ("mcp", "rag"):
            state["status"] = "ENVIRONMENT_CONTROLLED"
            state["detail"] = "No runtime switch; existing server environment applies"
        else:
            original = request("GET")
            state["original_enabled"] = original["enabled"]
            if original.get("locked"):
                raise ValueError("Mode is locked by deployment configuration")
            if not original["enabled"]:
                # Restore even if the server changes state but its response times out.
                restore = True
                request(method, json={"enabled": True})
            if not request("GET")["enabled"]:
                raise ValueError("Mode did not become enabled")
            state["status"] = "ENABLED"
        print(f"[{mode.upper()}][MODE] {state['status']}", flush=True)
        result = pipeline()
    except (requests.RequestException, ValueError) as error:
        state["status"] = "FAILED"
        state["error_type"] = type(error).__name__
        state["detail"] = "Check backend availability, authentication and deployment locks"
        result = {"service": service["name"], "feature": feature, "mode": mode, "execution_status": "MODE_FAILED", "validation_status": "FAIL", "model_status": "NOT_RUN", "human_review_required": True}
    finally:
        if restore:
            try:
                request(method, json={"enabled": False})
                if request("GET")["enabled"]:
                    raise ValueError("Mode was not restored")
                state["restored"] = True
            except (requests.RequestException, ValueError):
                state["restored"] = False
                print(f"[{mode.upper()}][RESTORE FAILED] Restore the feature switch manually", flush=True)
                if result is not None:
                    result["execution_status"] = "MODE_RESTORE_FAILED"
                    result["validation_status"] = "FAIL"
        if result is not None:
            result["feature_mode"] = state
    return result
