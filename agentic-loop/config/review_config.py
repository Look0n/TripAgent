IMPLEMENTATION_MODEL = "qwen2.5:0.5b"
REVIEW_MODEL = "llama3.1:8b"

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_TIMEOUT_SECONDS = 180

DB_PROMPTS = {
    "implementation": "implementation/database_task_prompt.txt",
    "review": "review/database_review_prompt.txt",
}

ENDPOINT_PROMPTS = {
    "implementation": "implementation/endpoints_task_prompt.txt",
    "review": "review/endpoints_review_prompt.txt",
}
ENDPOINT_TIMEOUT_SECONDS = 10

ARCHITECTURE_PROMPTS = {
    "system": "implementation/architecture_system_prompt.txt",
    "implementation": "implementation/architecture_task_prompt.txt",
    "review": "review/architecture_review_prompt.txt",
}
COMPOSE_TIMEOUT_SECONDS = 30

DEVOPS_PROMPTS = {
    "implementation": "implementation/devops_task_prompt.txt",
    "review": "review/devops_review_prompt.txt",
}
GITHUB_API_TIMEOUT_SECONDS = 20
CI_REPOSITORY = "Look0n/TripAgent"
CI_DEFAULT_BRANCH = "main"
