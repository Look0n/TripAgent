import os
import json

def save_report(data, filename="agentic_loop_execution.json"):
    os.makedirs("docs", exist_ok=True)
    report_path = os.path.join("docs", filename)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"[REPORTER] Report saved to {report_path}")