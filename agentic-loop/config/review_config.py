import os

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


MCP_SERVER_URL = os.getenv("LOOP_MCP_SERVER_URL", "http://localhost:7001/mcp")
RAG_SERVICE_URL = os.getenv("LOOP_RAG_SERVICE_URL", "http://localhost:7002").rstrip("/")
MCP_TIMEOUT_SECONDS = 30
RAG_TIMEOUT_SECONDS = 180
MCP_PROMPTS = {
    "implementation": "implementation/tool_selection_prompt.txt",
    "review": "review/integration_review_prompt.txt",
}
RAG_PROMPTS = {
    "implementation": "implementation/rag_implementation_prompt.txt",
    "review": "review/rag_review_prompt.txt",
    "reasoning": "review/rag_reasoning_prompt.txt",
}
