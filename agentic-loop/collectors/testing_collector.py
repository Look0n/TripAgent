import json
import re
import time
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

from core.reporter import repository_state
from core.validation import check, finish


def read_artifact(base, name, evidence):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Artifact path is required")
    path = (base / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(base):
        raise ValueError("Artifacts must stay inside the evidence directory")
    with path.open("rb") as stream:
        content = stream.read(2 * 1024 * 1024 + 1)
    if len(content) > 2 * 1024 * 1024:
        raise ValueError("Artifact exceeds 2 MiB")
    evidence.setdefault("artifacts", []).append({"path": name, "sha256": sha256(content).hexdigest()})
    return content.decode("utf-8-sig")


def collect_testing_context(feature, service_config, manifest_path, expected_commit=None):
    started = time.monotonic()
    evidence = {"checks": [], "source": "supplied-testing-evidence", "limitations": [
        "Files and commit/run metadata are supplied by the operator, not authenticated against GitHub.",
        "Endpoint-to-test mappings require human source review; passing mocked tests does not prove live inference.",
        "This reviews saved reports without executing tests, scanners, or deployment.",
    ]}
    path = Path(manifest_path).resolve()
    try:
        manifest = json.loads(read_artifact(path.parent, path.name, evidence))
        commit = expected_commit or repository_state()["commit"]
        evidence["expected_commit"] = commit
        evidence["provenance"] = {key: manifest.get(key) for key in ("feature", "commit", "ci")}
        check(evidence, "feature", manifest.get("feature") == feature)
        check(evidence, "commit", bool(commit) and bool(re.fullmatch(r"[0-9a-fA-F]{40}", str(manifest.get("commit", "")))) and manifest.get("commit") == commit)
        pre_commit = manifest.get("pre_commit", {})
        check(evidence, "scan_commit", pre_commit.get("commit") == commit and bool(commit))
        try:
            log = read_artifact(path.parent, pre_commit.get("log"), evidence)
            log = re.sub(r"\x1b\[[0-9;]*m", "", log)
            # Match hook summary lines, never an arbitrary 'Passed' elsewhere in a log.
            for name, pattern in (("ruff", r"ruff(?: check| scan)?"), ("detect-secrets", r"(?:detect[ -]secrets)(?: scan)?"), ("pip-audit", r"pip-audit(?: scan)?")):
                statuses = re.findall(r"^" + pattern + r"\.{2,}[^\r\n]*?\b(Passed|Failed|Skipped)\s*$", log, flags=re.I | re.M)
                statuses = [value.lower() for value in statuses]
                check(evidence, "pre_commit:" + name, bool(statuses) and all(value == "passed" for value in statuses), status="SKIP" if not statuses or ("skipped" in statuses and "failed" not in statuses) else None)
            check(evidence, "pre_commit_exit", pre_commit.get("exit_code") == 0)
        except FileNotFoundError:
            check(evidence, "pre_commit_log", False, "Scan log is missing", status="SKIP")
        ci = manifest.get("ci", {})
        check(evidence, "ci_commit", bool(commit) and ci.get("commit") == commit)
        check(evidence, "ci_workflow", ci.get("workflow") == service_config["ci_pipeline"])
        check(evidence, "ci_run", bool(re.fullmatch(r"https://github\.com/Look0n/TripAgent/actions/runs/[0-9]+", str(ci.get("run_url", "")))))
        check(evidence, "ci_conclusion", ci.get("conclusion") == "success", status="SKIP" if ci.get("conclusion") in (None, "queued", "in_progress") else None)
        reports = ci.get("junit", [])
        if not isinstance(reports, list) or len(reports) > 20:
            raise ValueError("Invalid JUnit list")
        check(evidence, "junit_reports", bool(reports), status="SKIP" if not reports else None)
        test_cases = {}
        for report in reports:
            try:
                xml = read_artifact(path.parent, report, evidence)
                if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
                    raise ValueError("XML declarations are not allowed")
                root = ET.fromstring(xml)
                if root.tag not in ("testsuite", "testsuites"):
                    raise ValueError("Expected a JUnit report")
                cases = list(root.iter("testcase"))
                check(evidence, "junit_nonempty:" + report, bool(cases), status="SKIP" if not cases else None)
                for suite in root.iter("testsuite"):
                    if "tests" in suite.attrib:
                        check(evidence, "junit_count:" + report, int(suite.get("tests")) == len(list(suite.iter("testcase"))))
                    if int(suite.get("skipped", 0)) > 0:
                        check(evidence, "junit_skipped:" + report, False, "Suite declares skipped tests", status="SKIP")
                for case in cases:
                    name = case.get("classname", "") + "::" + case.get("name", "")
                    status = "FAIL" if case.find("failure") is not None or case.find("error") is not None else "SKIP" if case.find("skipped") is not None else "PASS"
                    test_cases.setdefault(name, []).append(status)
                    check(evidence, "test:" + name, status == "PASS", status=status)
                # Collection errors can be recorded outside a testcase.
                check(evidence, "junit_errors:" + report, not list(root.iter("error")) and not list(root.iter("failure")) and all(int(suite.get("failures", 0)) == 0 and int(suite.get("errors", 0)) == 0 for suite in root.iter("testsuite")))
            except FileNotFoundError:
                check(evidence, "junit_file:" + report, False, "JUnit file is missing", status="SKIP")
        endpoints = ci.get("endpoints", [])
        identities = set()
        for endpoint in endpoints:
            identity = (endpoint.get("method"), endpoint.get("path"))
            valid = identity[0] in ("GET", "POST", "PUT", "PATCH", "DELETE") and isinstance(identity[1], str) and identity[1].startswith("/")
            check(evidence, "endpoint_identity", valid)
            if valid:
                identities.add(identity)
            names = endpoint.get("tests", [])
            check(evidence, "endpoint_tests:" + str(identity), isinstance(names, list) and bool(names) and all(test_cases.get(name) and all(value == "PASS" for value in test_cases[name]) for name in names), status="SKIP" if not test_cases else None)
        check(evidence, "two_endpoint_functions", len(identities) >= 2)
        evidence["test_summary"] = {status: sum(values.count(status) for values in test_cases.values()) for status in ("PASS", "FAIL", "SKIP")}
    except FileNotFoundError:
        check(evidence, "testing_manifest", False, "Evidence manifest is missing", status="SKIP")
    except (OSError, ValueError, TypeError, AttributeError, KeyError, ET.ParseError) as error:
        check(evidence, "testing_read", False, type(error).__name__ + ": invalid or unreadable testing evidence")
    return finish(evidence, started)
