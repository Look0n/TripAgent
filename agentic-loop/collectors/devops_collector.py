import os

def collect_devops_context(service_config):
    ci_path = service_config.get("ci_pipeline", "")
    exists = os.path.exists(ci_path)
    return f"CI/CD Pipeline: {ci_path} | Exists: {exists}"