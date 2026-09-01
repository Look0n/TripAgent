import sys
import os

# Добавляем корневую папку agentic-loop в пути Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.services import SERVICES
from pipelines.db_pipeline import run_db_pipeline
from pipelines.architecture_pipeline import run_architecture_pipeline
from pipelines.devops_pipeline import run_devops_pipeline
from core.reporter import save_report

def main():
    print("=== [STARTING AGENTIC LOOP] ===")
    results = {}
    
    for service_id, config in SERVICES.items():
        print(f"\n--- Processing Service: {config['name']} ---")
        
        db_res = run_db_pipeline(config)
        arch_res = run_architecture_pipeline(config)
        devops_res = run_devops_pipeline(config)
        
        results[service_id] = {
            "database_analysis": db_res,
            "architecture_analysis": arch_res,
            "devops_analysis": devops_res,
            "status": "COMPLETED"
        }
        
    save_report(results)
    print("\n=== [AGENTIC LOOP COMPLETED SUCCESSFULLY] ===")

if __name__ == "__main__":
    main()