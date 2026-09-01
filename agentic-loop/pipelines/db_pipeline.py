from collectors.db_collector import collect_db_context
from core.prompt_registry import load_prompt
from core.ai_runner import run_implementation, run_review

def run_db_pipeline(service_config):
    context = collect_db_context(service_config)
    prompt = load_prompt("db_prompt")
    
    impl_result = run_implementation(prompt, context)
    review_result = run_review("Review DB design:", impl_result)
    
    return {"impl": impl_result, "review": review_result}