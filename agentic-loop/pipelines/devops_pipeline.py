from collectors.devops_collector import collect_devops_context
from core.prompt_registry import load_prompt
from core.ai_runner import run_implementation, run_review

def run_devops_pipeline(service_config):
    context = collect_devops_context(service_config)
    prompt = load_prompt("devops_prompt")
    
    impl_result = run_implementation(prompt, context)
    review_result = run_review("Review DevOps setup:", impl_result)
    
    return {"impl": impl_result, "review": review_result}