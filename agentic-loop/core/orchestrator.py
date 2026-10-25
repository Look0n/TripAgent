import sys
import os
import argparse
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.services import SERVICES
from collectors.architecture_collector import collect_project_context
from pipelines.db_pipeline import run_db_pipeline
from pipelines.endpoints_pipeline import run_endpoints_pipeline
from pipelines.architecture_pipeline import run_architecture_pipeline
from pipelines.devops_pipeline import run_devops_pipeline
from pathlib import Path
from core.feature_modes import run_with_mode
from core.reporter import save_report, save_run_report, validation_passed
from pipelines.mcp_pipeline import run_mcp_pipeline
from pipelines.rag_pipeline import run_rag_pipeline
from pipelines.multi_agent_pipeline import run_multi_agent_pipeline
from pipelines.testing_pipeline import run_testing_pipeline

def evidence_path(feature):
    return str(Path(__file__).resolve().parents[2] / "evidence" / feature / "manifest.json")


def main():
    parser = argparse.ArgumentParser(description="TripAgent agentic loop")
    parser.add_argument("--mode", choices=("db", "endpoints", "architecture", "devops", "mcp", "rag", "multi-agent", "testing", "all"), default="all", help="Select analysis mode; all runs all eight review modes")
    parser.add_argument("--service", choices=tuple(SERVICES), help="Select one service; default is all five")
    parser.add_argument("--checks-only", action="store_true", help="Skip model review in MCP/RAG/Multi-Agent/Testing modes")
    parser.add_argument("--workflow-id", help="Existing workflow to review in multi-agent mode")
    parser.add_argument("--workflow-db", help="SQLite database or consistent backup for multi-agent mode")
    parser.add_argument("--evidence", help="Testing evidence JSON manifest")
    parser.add_argument("--commit", help="Expected full commit SHA for testing evidence; default is HEAD")
    args = parser.parse_args()
    if args.checks_only and args.mode not in ("mcp", "rag", "multi-agent", "testing"):
        parser.error("--checks-only requires mcp, rag, multi-agent or testing mode")
    if args.mode in ("multi-agent", "testing") and not args.service:
        parser.error("--service is required for evidence review")
    if (args.workflow_id or args.workflow_db) and args.mode not in ("multi-agent", "all"):
        parser.error("Workflow arguments require multi-agent mode")
    if (args.evidence or args.commit) and args.mode not in ("testing", "all"):
        parser.error("Evidence and commit arguments require testing mode")
    if args.mode == "all" and (args.workflow_id or args.evidence) and not args.service:
        parser.error("Explicit workflow/evidence in all mode requires --service")
    selected = {args.service: SERVICES[args.service]} if args.service else SERVICES
    print("=== [STARTING AGENTIC LOOP] ===")
    results = {}

    if args.mode in ("multi-agent", "testing"):
        config = SERVICES[args.service]
        if args.mode == "multi-agent":
            result = run_with_mode(config, args.service, "multi-agent", lambda: run_multi_agent_pipeline(config, args.service, args.workflow_id, database=args.workflow_db, checks_only=args.checks_only))
        else:
            result = run_testing_pipeline(config, args.service, args.evidence or evidence_path(args.service), expected_commit=args.commit, checks_only=args.checks_only)
        results[args.service] = result
        print(json.dumps(result, indent=2, ensure_ascii=False))
        save_run_report(results, mode=args.mode)
        return 0 if validation_passed(result, args.checks_only) else 1

    if args.mode in ("mcp", "rag"):
        pipeline = run_mcp_pipeline if args.mode == "mcp" else run_rag_pipeline
        for service_id, config in selected.items():
            results[service_id] = run_with_mode(config, service_id, args.mode, lambda: pipeline(config, service_id, checks_only=args.checks_only))
            print(json.dumps(results[service_id], indent=2, ensure_ascii=False))
        save_run_report(results, mode=args.mode)
        return 0 if all(validation_passed(result, args.checks_only) for result in results.values()) else 1

    if args.mode == "devops":
        for service_id, config in selected.items():
            print(f"[DEVOPS][START] {config['name']}", flush=True)
            results[service_id] = run_devops_pipeline(config)
            print(json.dumps(results[service_id], indent=2, ensure_ascii=False))
        save_run_report(results, mode="devops")
        return 0 if all(
            result["execution_status"] == "COMPLETED" and result.get("validation_status") == "PASS"
            for result in results.values()
        ) else 1

    if args.mode == "architecture":
        project_context = collect_project_context()
        for service_id, config in selected.items():
            print(f"[ARCHITECTURE][START] {config['name']}", flush=True)
            results[service_id] = run_architecture_pipeline(config, project_context=project_context)
            print(json.dumps(results[service_id], indent=2, ensure_ascii=False))
        save_run_report(results, mode="architecture")
        return 0 if all(
            result["execution_status"] == "COMPLETED" and result.get("validation_status") == "PASS"
            for result in results.values()
        ) else 1

    if args.mode == "endpoints":
        for service_id, config in selected.items():
            print(f"[ENDPOINTS][START] {config['name']}", flush=True)
            results[service_id] = run_endpoints_pipeline(config)
            print(json.dumps(results[service_id], indent=2, ensure_ascii=False))
        save_run_report(results, mode="endpoints")
        return 0 if all(
            result["execution_status"] == "COMPLETED" and result.get("validation_status") == "PASS"
            for result in results.values()
        ) else 1

    if args.mode == "db":
        for service_id, config in selected.items():
            print(f"[DB][START] {config['name']}", flush=True)
            results[service_id] = run_db_pipeline(config)
            print(json.dumps(results[service_id], indent=2, ensure_ascii=False))
        save_run_report(results)
        return 0 if all(result["status"] == "COMPLETED" for result in results.values()) else 1

    project_context = collect_project_context()
    for service_id, config in selected.items():
        print(f"\n--- Processing Service: {config['name']} ---")

        db_res = run_db_pipeline(config)
        endpoints_res = run_endpoints_pipeline(config)
        try:
            arch_res = run_architecture_pipeline(config, project_context=project_context)
        except (OSError, ValueError, RuntimeError) as error:
            arch_res = {"status": "FAILED", "error": str(error)}
        try:
            devops_res = run_devops_pipeline(config)
        except (OSError, ValueError, RuntimeError) as error:
            devops_res = {"status": "FAILED", "error": str(error)}

        mcp_res = run_with_mode(config, service_id, "mcp", lambda: run_mcp_pipeline(config, service_id))
        rag_res = run_with_mode(config, service_id, "rag", lambda: run_rag_pipeline(config, service_id))
        multi_agent_res = run_with_mode(config, service_id, "multi-agent", lambda: run_multi_agent_pipeline(config, service_id, args.workflow_id, database=args.workflow_db))
        testing_res = run_testing_pipeline(config, service_id, args.evidence or evidence_path(service_id), expected_commit=args.commit)
        results[service_id] = {
            "multi_agent_analysis": multi_agent_res,
            "testing_analysis": testing_res,
            "mcp_analysis": mcp_res,
            "rag_analysis": rag_res,
            "database_analysis": db_res,
            "endpoints_analysis": endpoints_res,
            "architecture_analysis": arch_res,
            "devops_analysis": devops_res,
            "status": "COMPLETED" if validation_passed(multi_agent_res) and validation_passed(testing_res) and validation_passed(mcp_res) and validation_passed(rag_res) and db_res.get("status") == "COMPLETED"
            and endpoints_res.get("execution_status") == "COMPLETED"
            and endpoints_res.get("validation_status") == "PASS"
            and arch_res.get("execution_status") == "COMPLETED"
            and arch_res.get("validation_status") == "PASS"
            and devops_res.get("execution_status") == "COMPLETED"
            and devops_res.get("validation_status") == "PASS" and all(
                result.get("status") != "FAILED" for result in (arch_res, devops_res)
            ) else "FAILED"
        }

    report_keys = {
        "db": "database_analysis",
        "endpoints": "endpoints_analysis",
        "architecture": "architecture_analysis",
        "devops": "devops_analysis",
        "multi-agent": "multi_agent_analysis",
        "testing": "testing_analysis",
        "mcp": "mcp_analysis",
        "rag": "rag_analysis",
    }
    for mode, result_key in report_keys.items():
        save_run_report({key: value[result_key] for key, value in results.items()}, mode=mode)
    save_report(results)
    print("\n=== [AGENTIC LOOP FINISHED - CHECK INDIVIDUAL RESULTS] ===")
    return 0 if all(result["status"] == "COMPLETED" for result in results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
