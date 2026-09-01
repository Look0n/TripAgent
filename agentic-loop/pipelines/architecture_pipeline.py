from collectors.architecture_collector import collect_architecture_context
from collectors.endpoints_collector import collect_endpoints_context
from core.prompt_registry import load_prompt
from core.ai_runner import run_implementation, run_review

def run_architecture_pipeline(service_config):
    arch_ctx = collect_architecture_context(service_config)
    ep_ctx = collect_endpoints_context(service_config)
    full_ctx = f"{arch_ctx}\n{ep_ctx}"
    
    prompt = load_prompt("arch_prompt")
    impl_result = run_implementation(prompt, full_ctx)
    review_result = run_review("Review Code Architecture:", impl_result)
    
    return {"impl": impl_result, "review": review_result}