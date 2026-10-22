# Environment switches for the Attractions AI services.
# Locally AI-Mode, MCP and RAG are on by default; CI and the cloud baseline
# turn them off. Multi-Agent is off at startup and can be locked off entirely.

import os


TRUE_VALUES = ("1", "true", "yes", "on")


def env_flag(name, default):
    return os.getenv(name, default).strip().lower() in TRUE_VALUES


def ai_mode_enabled():
    return env_flag("AI_MODE_ENABLED", "true")


def mcp_enabled():
    return env_flag("MCP_ENABLED", "true")


def rag_enabled():
    return env_flag("RAG_ENABLED", "true")


def multi_agent_locked():
    return env_flag("MULTI_AGENT_LOCKED", "false")


def service_modes(multi_agent_on):
    return {
        "ai_mode": ai_mode_enabled(),
        "mcp": mcp_enabled(),
        "rag": rag_enabled(),
        "multi_agent": multi_agent_on and not multi_agent_locked(),
        "multi_agent_locked": multi_agent_locked(),
    }
