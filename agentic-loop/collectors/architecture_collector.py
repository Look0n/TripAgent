import os

def collect_architecture_context(service_config):
    path = service_config.get("path", "")
    if os.path.exists(path):
        files = os.listdir(path)
        return f"Structure of {path}: {', '.join(files)}"
    return f"Path {path} not found"