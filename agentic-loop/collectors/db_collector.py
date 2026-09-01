import os

def collect_db_context(service_config):
    db_path = service_config.get("db_path", "")
    exists = os.path.exists(db_path)
    return f"DB File: {db_path} | Exists: {exists}"