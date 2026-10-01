import base64
from datetime import datetime, timezone
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
from urllib import error, parse, request

from config.review_config import CI_REPOSITORY, CI_DEFAULT_BRANCH, GITHUB_API_TIMEOUT_SECONDS


REPO_ROOT = Path(__file__).resolve().parents[2]


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github_json(path):
    if not path.startswith(f"/repos/{CI_REPOSITORY}/"):
        raise ValueError("GitHub read must target the configured repository")
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request("https://api.github.com" + path, headers=headers, method="GET")
    try:
        with request.build_opener(NoRedirect()).open(req, timeout=GITHUB_API_TIMEOUT_SECONDS) as response:
            raw = response.read(4_194_305)
        if len(raw) > 4_194_304:
            raise ValueError("GitHub response exceeds 4 MiB limit")
        return json.loads(raw)
    except error.HTTPError as exc:
        raise RuntimeError(f"GitHub HTTP {exc.code}; repository access, run existence or rate limit requires checking") from exc
    except (error.URLError, OSError, ValueError) as exc:
        raise RuntimeError(f"GitHub evidence unavailable: {type(exc).__name__}") from exc


def github_pages(path, key):
    items = []
    for page in range(1, 11):
        data = github_json(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
        batch = data.get(key)
        if not isinstance(batch, list):
            raise ValueError(f"Invalid GitHub {key} response")
        items.extend(batch)
        if len(items) >= data.get("total_count", len(items)) or len(batch) < 100:
            return items, True
    return items, False


def git_read(arguments):
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={REPO_ROOT}", *arguments],
            cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def parse_workflow(text):
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("Install agentic-loop/requirements.txt before running DevOps mode") from exc
    if len(text) > 1_048_576:
        raise ValueError("Workflow exceeds 1 MiB limit")
    try:
        data = yaml.load(text, Loader=yaml.BaseLoader)
    except yaml.YAMLError as exc:
        raise ValueError("Invalid workflow YAML") from exc
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), dict) or not data["jobs"]:
        raise ValueError("Workflow must contain a non-empty jobs mapping")
    return data


def inspect_workflow(text, service_config):
    data = parse_workflow(text)
    triggers = data.get("on", {})
    if isinstance(triggers, str):
        triggers = {triggers: {}}
    elif isinstance(triggers, list):
        triggers = {name: {} for name in triggers}
    if not isinstance(triggers, dict):
        raise ValueError("Unsupported workflow triggers")
    result = {"name": data.get("name"), "triggers": list(triggers), "jobs": [], "findings": []}
    if not triggers:
        result["findings"].append({"status": "FAIL", "issue": "No trigger defined"})
    workflow_path = service_config["ci_pipeline"]
    for event, options in triggers.items():
        if isinstance(options, dict) and isinstance(options.get("paths"), list):
            paths = options["paths"]
            covered = any(fnmatch.fnmatchcase(workflow_path, path) for path in paths if not path.startswith("!"))
            if not covered:
                result["findings"].append({"status": "WARNING", "issue": f"{event} paths do not explicitly cover this workflow file", "paths": paths})
    all_scripts = []
    for job_id, job in data["jobs"].items():
        if not isinstance(job, dict):
            raise ValueError("Invalid job mapping")
        steps = job.get("steps", [])
        if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
            raise ValueError("Invalid workflow steps")
        scripts = [step.get("run", "") for step in steps]
        all_scripts.extend(scripts)
        result["jobs"].append({
            "id": job_id, "name": job.get("name", job_id), "needs": job.get("needs", []),
            "reusable_workflow": bool(job.get("uses")),
            "steps": [{"name": step.get("name", "(unnamed)"), "action": step.get("uses"),
                       "condition": step.get("if"), "has_run": bool(step.get("run"))} for step in steps],
        })
    script = "\n".join(all_scripts)
    result["declared_checks"] = {
        "image_build_command": bool(re.search(r"docker\s+(?:build|compose\s+build)", script)),
        "compose_validation_command": bool(re.search(r"docker\s+compose\s+config", script)),
        "http_checks": "curl " in script,
        "pytest_command": bool(re.search(r"\bpytest\b", script)),
        "seed_count_check": bool(re.search(r"COUNT|seed|records", script, re.I)),
        "artifact_upload": any("actions/upload-artifact@" in (step.get("action") or "") for job in result["jobs"] for step in job["steps"]),
        "always_condition_present": any("always()" in (step.get("condition") or "") for job in result["jobs"] for step in job["steps"]),
    }
    result["interpretation"] = "Declared command patterns only; not proof of successful execution or complete shell analysis"
    if service_config.get("student_id") == "14582668":
        backend_ports = sorted(set(re.findall(r"http://localhost:(\d+)/(?:health|api/checklist-items)", script)))
        unexpected = [port for port in backend_ports if port not in ("3004", "5004", "6004")]
        mappings = re.findall(r"-p\s+(\d+):(\d+)", script)
        if unexpected or any(pair not in (("3004", "3004"), ("5004", "5004"), ("6004", "6004")) for pair in mappings):
            result["findings"].append({"status": "FAIL", "issue": "Checklist CI literal ports disagree with 3004/5004/6004 contract", "unexpected_url_ports": unexpected, "port_mappings": mappings})
    result["status"] = "FAIL" if any(item["status"] == "FAIL" for item in result["findings"]) else "PASS"
    return result


def collect_devops_context(service_config, run_id=None, branch=CI_DEFAULT_BRANCH, offline=False):
    evidence = {
        "service": service_config["name"], "repository": CI_REPOSITORY,
        "workflow_path": service_config["ci_pipeline"],
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "ci_status": "NOT_CHECKED", "evidence_status": "UNAVAILABLE",
        "version_status": "UNAVAILABLE", "validation_status": "PARTIAL",
        "not_verified": ["artifact contents", "raw job logs", "new CI execution", "current uncommitted code passing CI", "live user AI-mode", "exact executed workflow revision for pull-request merge refs"],
    }
    path = (REPO_ROOT / service_config["ci_pipeline"]).resolve()
    if not path.is_relative_to(REPO_ROOT) or not path.is_file():
        evidence["error"] = "Workflow file missing or outside repository"
        evidence["validation_status"] = "UNAVAILABLE"
        return False, evidence
    text = path.read_text(encoding="utf-8")
    evidence["workflow"] = inspect_workflow(text, service_config)
    head = git_read(["rev-parse", "HEAD"])
    dirty = git_read(["status", "--porcelain"])
    evidence["local"] = {"head_sha": head, "working_tree_dirty": None if dirty is None else bool(dirty)}
    if offline:
        evidence["selection"] = "Offline; no GitHub request"
        evidence["validation_status"] = "FAIL" if evidence["workflow"]["status"] == "FAIL" else "PARTIAL"
        return True, evidence
    prefix = f"/repos/{CI_REPOSITORY}"
    try:
        if run_id is not None:
            if not str(run_id).isdigit() or int(run_id) <= 0:
                raise ValueError("run_id must be a positive integer")
            run = github_json(f"{prefix}/actions/runs/{int(run_id)}")
            evidence["selection"] = "Explicit run ID"
        else:
            filename = parse.quote(Path(service_config["ci_pipeline"]).name, safe="")
            query = parse.urlencode({"branch": branch, "per_page": 1})
            runs = github_json(f"{prefix}/actions/workflows/{filename}/runs?{query}").get("workflow_runs", [])
            evidence["selection"] = f"Latest run returned for workflow on branch {branch}; not latest successful run"
            if not runs:
                raise RuntimeError("No workflow run found on selected branch")
            run = runs[0]
        if run.get("path", "").split("@")[0] != service_config["ci_pipeline"]:
            raise ValueError("Selected run belongs to a different workflow")
        repository = run.get("repository", {}).get("full_name", "")
        if repository.lower() != CI_REPOSITORY.lower():
            raise ValueError("Selected run belongs to a different repository")
        identifier, attempt = run["id"], run["run_attempt"]
        evidence["run"] = {key: run.get(key) for key in ("id", "run_attempt", "name", "path", "event", "head_branch", "head_sha", "status", "conclusion", "created_at", "updated_at", "html_url")}
        evidence["ci_status"] = "PENDING" if run["status"] != "completed" else "PASS" if run.get("conclusion") == "success" else "FAIL"
        evidence["version_status"] = (
            "UNAVAILABLE" if head is None or dirty is None else
            "LOCAL_CHANGES" if dirty else "MATCH" if head == run["head_sha"] else "DIFFERENT_COMMIT"
        )
        problems = []
        try:
            jobs, complete = github_pages(f"{prefix}/actions/runs/{identifier}/attempts/{attempt}/jobs", "jobs")
            evidence["jobs"] = [
                {"id": job.get("id"), "name": job.get("name"), "status": job.get("status"), "conclusion": job.get("conclusion"),
                 "steps": [{key: step.get(key) for key in ("name", "number", "status", "conclusion")} for step in job.get("steps", [])]}
                for job in jobs
            ]
            if not complete or not jobs:
                problems.append("Job evidence empty or pagination limit reached")
            if any(job.get("conclusion") in ("failure", "timed_out", "cancelled") for job in jobs):
                evidence["ci_status"] = "FAIL"
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            problems.append(f"Jobs unavailable: {type(exc).__name__}")
        try:
            artifacts, complete = github_pages(f"{prefix}/actions/runs/{identifier}/artifacts", "artifacts")
            evidence["artifacts"] = [{key: item.get(key) for key in ("id", "name", "expired", "size_in_bytes", "created_at")} for item in artifacts]
            if not complete or not artifacts or any(item.get("expired") for item in artifacts):
                problems.append("Artifact evidence missing, expired, or incomplete")
            if attempt > 1:
                problems.append("Artifact listing is run-level; attribution to this attempt is unverified")
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            problems.append(f"Artifacts unavailable: {type(exc).__name__}")
        try:
            source = github_json(f"{prefix}/contents/{service_config['ci_pipeline']}?ref={parse.quote(run['head_sha'], safe='')}")
            if source.get("encoding") != "base64":
                raise ValueError("Unsupported workflow content encoding")
            remote_text = base64.b64decode(source["content"], validate=False).decode("utf-8")
            evidence["workflow_matches_run_commit"] = text.replace("\r\n", "\n") == remote_text.replace("\r\n", "\n")
            evidence["run_commit_workflow"] = inspect_workflow(remote_text, service_config)
            if not evidence["workflow_matches_run_commit"]:
                problems.append("Local workflow differs from workflow at run head SHA")
        except (RuntimeError, ValueError, KeyError, TypeError) as exc:
            problems.append(f"Run-commit workflow unavailable: {type(exc).__name__}")
        evidence["evidence_status"] = "COMPLETE_METADATA" if not problems else "PARTIAL"
        evidence["limitations"] = problems
    except (RuntimeError, ValueError, KeyError, TypeError) as exc:
        evidence["error"] = str(exc)
    evidence["validation_status"] = (
        "FAIL" if evidence["workflow"]["status"] == "FAIL" or evidence["ci_status"] == "FAIL" else
        "PASS" if evidence["ci_status"] == "PASS" and evidence["version_status"] == "MATCH"
        and evidence["evidence_status"] == "COMPLETE_METADATA" else "PARTIAL"
    )
    return True, evidence
