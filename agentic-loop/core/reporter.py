import os
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def save_run_report(data, mode="db"):
    if mode not in ("db", "endpoints", "architecture", "devops"):
        raise ValueError("Unsupported report mode")
    directory = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "agentic-loop" / "runs"
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{mode}-{timestamp}-{uuid4().hex[:8]}.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
    print(f"[REPORTER] Report saved to {path}", flush=True)
    return path

def save_report(data, filename="agentic_loop_execution.json"):
    os.makedirs("docs", exist_ok=True)
    report_path = os.path.join("docs", filename)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[REPORTER] Report saved to {report_path}")
