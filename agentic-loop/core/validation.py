import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check(evidence, name, passed, detail=None, status=None):
    evidence["checks"].append({"id": name, "status": status or ("PASS" if passed else "FAIL"), "detail": detail})


def finish(evidence, started):
    statuses = [row["status"] for row in evidence["checks"]]
    evidence["validation_status"] = "FAIL" if "FAIL" in statuses else "PARTIAL" if "SKIP" in statuses or not statuses else "PASS"
    evidence["duration_seconds"] = round(time.monotonic() - started, 3)
    return evidence["validation_status"] == "PASS", evidence


def sanitise(value):
    if isinstance(value, dict):
        hidden = {"password", "token", "access_token", "refresh_token", "authorization", "cookie", "secret", "api_key", "email", "first_name", "last_name", "profile", "preferences", "customer_id"}
        return {str(k): "[REDACTED]" if str(k).lower() in hidden else sanitise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitise(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[REDACTED]", value)
        return re.sub(r"(?i)(bearer\s+)[^\s]+", r"\1[REDACTED]", value)
    return value


def structure(evidence, paths):
    for path in paths:
        check(evidence, f"file:{path}", (ROOT / path).is_file())
