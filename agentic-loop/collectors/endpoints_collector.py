import os

def collect_endpoints_context(service_config):
    backend_path = service_config.get("backend_path", "")
    if os.path.exists(backend_path):
        with open(backend_path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[:500]
    return "Backend file not found"