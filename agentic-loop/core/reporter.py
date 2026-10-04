from core.validation import sanitise
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def save_run_report(data, mode="db"):
    if mode not in ("db", "endpoints", "architecture", "devops", "mcp", "rag"):
        raise ValueError("Unsupported report mode")
    directory = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "agentic-loop" / "runs"
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{mode}-{timestamp}-{uuid4().hex[:8]}.json"
    if mode in ("mcp", "rag"):
        data = {"run_id": path.stem, "mode": mode, "source": "live-services", "repository": repository_state(), "results": sanitise(data)}
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
    if mode in ("mcp", "rag"):
        with path.with_suffix(".md").open("x", encoding="utf-8") as stream:
            stream.write(validation_markdown(data))
    print(f"[REPORTER] Report saved to {path}", flush=True)
    return path

def save_report(data, filename="agentic_loop_execution.json"):
    os.makedirs("docs", exist_ok=True)
    report_path = os.path.join("docs", filename)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[REPORTER] Report saved to {report_path}")


def repository_state():
    import subprocess
    root = Path(__file__).resolve().parents[2]
    def git(*args):
        return subprocess.check_output(["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
    try:
        return {"commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain"))}
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "dirty": None}


def validation_passed(result, checks_only=False):
    return result.get("execution_status") == "COMPLETED" and result.get("validation_status") == "PASS" and (checks_only or (result.get("model_status") == "COMPLETED" and bool(result.get("output_checks")) and all(result["output_checks"].values())))


def validation_markdown(data):
    lines = [f"# {data['mode'].upper()} validation", "", f"Run: {data['run_id']}", f"Repository: {json.dumps(data['repository'])}", "", "Automated checks and model opinions are separate. Human approval is not implied.", ""]
    for feature, result in data["results"].items():
        lines.extend([f"## {feature}", "", f"Execution: {result.get('execution_status')}", f"Validation: {result.get('validation_status')}", f"Models: {result.get('model_status')}", ""])
        for item in result.get("evidence", {}).get("checks", []):
            lines.append(f"- {item['status']}: {item['id']}")
        for query in result.get("evidence", {}).get("queries", []):
            lines.extend(["", f"Query: {query['case']['query']}", f"Metrics: {json.dumps(query.get('metrics', {}))}"])
        lines.extend(["", "### Implementation", "", result.get("impl", "Not run"), "", "### Review", "", result.get("review", "Not run"), "", "### Limitations", ""])
        lines.extend(f"- {value}" for value in result.get("evidence", {}).get("limitations", []))
        lines.append("")
    return "\n".join(lines)
