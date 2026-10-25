from datetime import datetime, timezone
import json

from config.review_config import IMPLEMENTATION_MODEL, REVIEW_MODEL
from core.ai_runner import run_implementation, run_review
from core.prompt_registry import load_prompt, render_prompt
from core.validation import sanitise


def run_evidence_pipeline(service_config, feature, mode, collector, prompts, checks_only=False):
    result = {"service": service_config["name"], "feature": feature, "mode": mode, "started_at": datetime.now(timezone.utc).isoformat(), "execution_status": "STARTED", "validation_status": "FAIL", "model_status": "NOT_RUN", "human_review_required": True, "stages": {}}
    stage = "observe"
    try:
        print(f"[{mode.upper()}][OBSERVE] Collecting saved evidence", flush=True)
        _, evidence = collector()
        evidence = sanitise(evidence)
        result["evidence"] = evidence
        result["validation_status"] = evidence["validation_status"]
        result["stages"][stage] = "COLLECTED"
        if not checks_only:
            stage = "prompts"
            values = {"REVIEW_TARGET": service_config["name"], "VALIDATION_EVIDENCE": json.dumps(evidence, ensure_ascii=False)}
            implementation_prompt = render_prompt(load_prompt(prompts["implementation"]), values)
            review_template = load_prompt(prompts["review"])
            render_prompt(review_template, {**values, "IMPLEMENTATION_RECOMMENDATION": "Pending"})
            result["prompt_files"] = dict(prompts)
            result["models"] = {"implementation": IMPLEMENTATION_MODEL, "review": REVIEW_MODEL}
            result["stages"][stage] = "PASSED"
            stage = "implementation"
            result["model_status"] = "RUNNING"
            print(f"[{mode.upper()}][IMPLEMENTATION] Calling {IMPLEMENTATION_MODEL}", flush=True)
            result["impl"] = sanitise(run_implementation(implementation_prompt))
            result["stages"][stage] = "PASSED"
            stage = "review"
            review_prompt = render_prompt(review_template, {**values, "IMPLEMENTATION_RECOMMENDATION": result["impl"]})
            print(f"[{mode.upper()}][REVIEW] Calling {REVIEW_MODEL}", flush=True)
            result["review"] = sanitise(run_review(review_prompt))
            result["stages"][stage] = "PASSED"
            result["model_status"] = "COMPLETED"
            result["output_checks"] = {"implementation_nonempty": bool(result["impl"].strip()), "review_sections": all(label in result["review"] for label in ("Strengths:", "Risk:", "Correction:", "Retest:"))}
        result["execution_status"] = "COMPLETED"
    except Exception as error:
        result["execution_status"] = stage.upper() + "_FAILED"
        result["stages"][stage] = "FAILED"
        result["error"] = {"type": type(error).__name__, "message": "Review stage failed; inspect recorded checks"}
        if stage in ("implementation", "review"):
            result["model_status"] = "FAILED"
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    return result
