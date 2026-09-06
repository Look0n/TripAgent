from datetime import datetime, timezone
import json

from collectors.devops_collector import collect_devops_context
from config.review_config import DEVOPS_PROMPTS, IMPLEMENTATION_MODEL, REVIEW_MODEL
from core.prompt_registry import load_prompt, render_prompt
from core.ai_runner import run_implementation, run_review


def run_devops_pipeline(service_config, checks_only=False, run_id=None, branch="main", offline=False):
    result = {
        "service": service_config["name"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "execution_status": "STARTED",
        "model_status": "NOT_RUN",
        "human_review_required": not checks_only,
        "stages": {},
    }
    stage = "observe"
    try:
        print("[DEVOPS][OBSERVE] Reading workflow and GitHub CI evidence", flush=True)
        available, evidence = collect_devops_context(service_config, run_id=run_id, branch=branch, offline=offline)
        result["evidence"] = evidence
        result["validation_status"] = evidence["validation_status"]
        if not available:
            raise RuntimeError("No usable workflow evidence; see evidence")
        result["stages"][stage] = "COLLECTED"
        if not checks_only:
            stage = "prompts"
            templates = {key: load_prompt(path) for key, path in DEVOPS_PROMPTS.items()}
            values = {"REVIEW_TARGET": service_config["name"], "VALIDATION_EVIDENCE": json.dumps(evidence, ensure_ascii=False)}
            impl_prompt = render_prompt(templates["implementation"], values)
            render_prompt(templates["review"], {**values, "IMPLEMENTATION_RECOMMENDATION": "Pending"})
            result["prompt_files"] = dict(DEVOPS_PROMPTS)
            result["models"] = {"implementation": IMPLEMENTATION_MODEL, "review": REVIEW_MODEL}
            result["stages"][stage] = "PASSED"
            stage = "implementation"
            result["model_status"] = "RUNNING"
            print(f"[DEVOPS][IMPLEMENTATION] Calling {IMPLEMENTATION_MODEL}", flush=True)
            result["implementation_prompt"] = impl_prompt
            result["impl"] = run_implementation(impl_prompt)
            result["stages"][stage] = "PASSED"
            stage = "review"
            review_prompt = render_prompt(templates["review"], {**values, "IMPLEMENTATION_RECOMMENDATION": result["impl"]})
            result["review_prompt"] = review_prompt
            print(f"[DEVOPS][REVIEW] Calling {REVIEW_MODEL}", flush=True)
            result["review"] = run_review(review_prompt)
            result["stages"][stage] = "PASSED"
            result["model_status"] = "COMPLETED"
            result["output_checks"] = {
                "implementation_within_60_words": len(result["impl"].split()) <= 60,
                "review_within_35_words": len(result["review"].split()) <= 35,
            }
        result["execution_status"] = "COMPLETED"
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
        result["stages"][stage] = "FAILED"
        result["execution_status"] = f"{stage.upper()}_FAILED"
        result["error"] = str(error)
        if stage in ("implementation", "review"):
            result["model_status"] = "FAILED"
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    print(f"[DEVOPS][{result['execution_status']}] CI evidence: {result.get('validation_status', 'UNAVAILABLE')}", flush=True)
    return result
