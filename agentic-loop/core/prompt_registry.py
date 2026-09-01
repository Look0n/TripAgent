import os

def load_prompt(prompt_name):
    prompt_path = os.path.join("prompts", "service", f"{prompt_name}.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Analyze the provided input and generate feedback."