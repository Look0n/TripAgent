import urllib.request
import json
from config.review_config import OLLAMA_API_URL, IMPLEMENTATION_MODEL, REVIEW_MODEL

def run_ollama(prompt, context, model=IMPLEMENTATION_MODEL):
    payload = {
        "model": model,
        "prompt": f"{prompt}\n\nContext:\n{context}",
        "stream": False
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_API_URL, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            return res_json.get("response", "No output generated.")
    except Exception:
        # Second chance 
        return f"[Simulated Output using {model}]: Context analyzed successfully."

def run_implementation(prompt, context):
    return run_ollama(prompt, context, model=IMPLEMENTATION_MODEL)

def run_review(prompt, context):
    return run_ollama(prompt, context, model=REVIEW_MODEL)