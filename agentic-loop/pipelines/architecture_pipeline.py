from datetime import datetime, timezone
import json

from collectors.architecture_collector import collect_architecture_context
from config.review_config import ARCHITECTURE_PROMPTS, IMPLEMENTATION_MODEL, REVIEW_MODEL
from core.prompt_registry import load_prompt, render_prompt
from core.ai_runner import run_implementation, run_review


def run_architecture_pipeline(service_config, checks_only=False, project_context=None):
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
        print("[ARCHITECTURE][OBSERVE] Inspecting files, Compose configuration and runtime", flush=True)
        available, evidence = collect_architecture_context(service_config, project_context)
        result["evidence"] = evidence
        result["validation_status"] = evidence["validation_status"]
        if not available:
            raise RuntimeError("No usable Compose configuration; see architecture evidence")
        result["stages"][stage] = "COLLECTED"
        if not checks_only:
            stage = "prompts"
            templates = {key: load_prompt(path) for key, path in ARCHITECTURE_PROMPTS.items()}
            values = {"REVIEW_TARGET": service_config["name"], "VALIDATION_EVIDENCE": json.dumps(evidence, ensure_ascii=False)}
            impl_prompt = templates["system"] + "\n\n" + render_prompt(templates["implementation"], values)
            render_prompt(templates["review"], {**values, "IMPLEMENTATION_RECOMMENDATION": "Pending"})
            result["prompt_files"] = dict(ARCHITECTURE_PROMPTS)
            result["models"] = {"implementation": IMPLEMENTATION_MODEL, "review": REVIEW_MODEL}
            result["stages"][stage] = "PASSED"
            stage = "implementation"
            result["model_status"] = "RUNNING"
            print(f"[ARCHITECTURE][IMPLEMENTATION] Calling {IMPLEMENTATION_MODEL}", flush=True)
            result["implementation_prompt"] = impl_prompt
            result["impl"] = run_implementation(impl_prompt)
            result["stages"][stage] = "PASSED"
            stage = "review"
            review_prompt = render_prompt(templates["review"], {**values, "IMPLEMENTATION_RECOMMENDATION": result["impl"]})
            result["review_prompt"] = review_prompt
            print(f"[ARCHITECTURE][REVIEW] Calling {REVIEW_MODEL}", flush=True)
            result["review"] = run_review(review_prompt)
            result["stages"][stage] = "PASSED"
            result["model_status"] = "COMPLETED"
            result["output_checks"] = {
                "implementation_within_60_words": len(result["impl"].split()) <= 60,
                "review_within_35_words": len(result["review"].split()) <= 35,
            }
        result["execution_status"] = "COMPLETED"
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        result["stages"][stage] = "FAILED"
        result["execution_status"] = f"{stage.upper()}_FAILED"
        result["error"] = str(error)
        if stage in ("implementation", "review"):
            result["model_status"] = "FAILED"
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    print(f"[ARCHITECTURE][{result['execution_status']}] Architecture: {result.get('validation_status', 'UNAVAILABLE')}", flush=True)
    return result
