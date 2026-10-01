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
from core.reporter import save_report, save_run_report

def main():
    parser = argparse.ArgumentParser(description="TripAgent agentic loop")
    parser.add_argument("--mode", choices=("db", "endpoints", "architecture", "devops", "all"), default="all", help="Select analysis mode")
    parser.add_argument("--service", choices=tuple(SERVICES), help="Select one service; default is all five")
    args = parser.parse_args()
    selected = {args.service: SERVICES[args.service]} if args.service else SERVICES
    print("=== [STARTING AGENTIC LOOP] ===")
    results = {}

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

        results[service_id] = {
            "database_analysis": db_res,
            "endpoints_analysis": endpoints_res,
            "architecture_analysis": arch_res,
            "devops_analysis": devops_res,
            "status": "COMPLETED" if db_res.get("status") == "COMPLETED"
            and endpoints_res.get("execution_status") == "COMPLETED"
            and endpoints_res.get("validation_status") == "PASS"
            and arch_res.get("execution_status") == "COMPLETED"
            and arch_res.get("validation_status") == "PASS"
            and devops_res.get("execution_status") == "COMPLETED"
            and devops_res.get("validation_status") == "PASS" and all(
                result.get("status") != "FAILED" for result in (arch_res, devops_res)
            ) else "FAILED"
        }

    save_report(results)
    print("\n=== [AGENTIC LOOP FINISHED - CHECK INDIVIDUAL RESULTS] ===")
    return 0 if all(result["status"] == "COMPLETED" for result in results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
