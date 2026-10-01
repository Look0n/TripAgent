from datetime import datetime, timezone
from pathlib import Path

from collectors.db_collector import collect_db_context
from config.review_config import DB_PROMPTS, IMPLEMENTATION_MODEL, REVIEW_MODEL
from core.prompt_registry import load_prompt, render_prompt
from core.ai_runner import run_implementation, run_review


def run_db_pipeline(service_config):
    result = {
        "service": service_config["name"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "models": {"implementation": IMPLEMENTATION_MODEL, "review": REVIEW_MODEL},
        "prompt_files": dict(DB_PROMPTS),
        "stages": {},
        "human_review_required": True,
    }
    stage = "observe"
    try:
        print("[DB][OBSERVE] Querying live database", flush=True)
        ok, evidence = collect_db_context(service_config, Path(__file__).resolve().parents[2])
        result["evidence"] = evidence
        if not ok:
            raise RuntimeError(evidence)
        result["stages"][stage] = "PASSED"
        stage = "prompts"
        templates = {key: load_prompt(path) for key, path in DB_PROMPTS.items()}
        values = {"REVIEW_TARGET": service_config["name"], "VALIDATION_EVIDENCE": evidence}
        implementation_prompt = render_prompt(templates["implementation"], values)
        render_prompt(templates["review"], {**values, "IMPLEMENTATION_RECOMMENDATION": "Pending"})
        result["stages"][stage] = "PASSED"
        stage = "implementation"
        print(f"[DB][IMPLEMENTATION] Calling {IMPLEMENTATION_MODEL}", flush=True)
        result["implementation_prompt"] = implementation_prompt
        result["impl"] = run_implementation(implementation_prompt)
        result["stages"][stage] = "PASSED"
        stage = "review"
        review_prompt = render_prompt(templates["review"], {
            **values, "IMPLEMENTATION_RECOMMENDATION": result["impl"],
        })
        result["review_prompt"] = review_prompt
        print(f"[DB][REVIEW] Calling {REVIEW_MODEL}", flush=True)
        result["review"] = run_review(review_prompt)
        result["stages"][stage] = "PASSED"
        result["status"] = "COMPLETED"
        result["output_checks"] = {
            "implementation_within_60_words": len(result["impl"].split()) <= 60,
            "review_within_35_words": len(result["review"].split()) <= 35,
        }
    except (OSError, ValueError, RuntimeError) as error:
        result["stages"][stage] = "FAILED"
        result["status"] = f"{stage.upper()}_FAILED"
        result["error"] = str(error)
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    print(f"[DB][{result['status']}]", flush=True)
    return result
