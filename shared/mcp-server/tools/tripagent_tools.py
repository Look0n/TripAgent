from services.tripagent_client import (
    TripAgentServiceError,
    check_service_health,
    list_services,
)
from tool_registry import get_tools_for_feature


def list_tripagent_services() -> dict:
    """
    List the feature services registered with TripAgent.
    """

    return {
        "success": True,
        "services": list_services(),
    }


def get_service_status(service_name: str) -> dict:
    """
    Check whether a TripAgent feature service is available.
    """

    try:
        status = check_service_health(service_name)

        return {
            "success": True,
            **status,
        }

    except TripAgentServiceError as exc:
        return {
            "success": False,
            "error": str(exc),
        }


def list_available_tools(
    feature: str = "account",
) -> dict:
    """
    Return the MCP tools available to a TripAgent feature.
    """

    tools = get_tools_for_feature(feature)

    return {
        "success": True,
        "feature": feature,
        "count": len(tools),
        "tools": tools,
    }


def get_tripagent_help(
    topic: str = "general",
) -> dict:
    """
    Return general information about TripAgent.
    """

    topics = {
        "general": (
            "TripAgent is composed of multiple travel-related "
            "features connected through shared infrastructure."
        ),

        "account": (
            "The Account feature manages customer profiles "
            "and travel preferences."
        ),

        "accommodation": (
            "The Accommodation feature provides "
            "accommodation-related functionality."
        ),

        "attractions": (
            "The Attractions feature provides "
            "attraction-related functionality."
        ),

        "checklist": (
            "The Checklist feature supports travel "
            "checklist functionality."
        ),

        "flight": (
            "The Flight feature provides "
            "flight-related functionality."
        ),

        "mcp": (
            "The shared MCP server provides controlled tools "
            "that TripAgent features can use."
        ),

        "rag": (
            "The shared RAG service provides retrieval-"
            "augmented access to TripAgent knowledge."
        ),
    }

    topic = topic.strip().lower()

    return {
        "success": True,
        "topic": topic,
        "help": topics.get(
            topic,
            "No help is available for that topic.",
        ),
    }


def get_system_summary() -> dict:
    """
    Return non-sensitive information about TripAgent's
    shared architecture.
    """

    services = list_services()

    return {
        "success": True,

        "system": "TripAgent",

        "features": [
            service["id"]
            for service in services
        ],

        "feature_count": len(services),

        "shared_services": {
            "mcp": {
                "port": 7001,
                "transport": "streamable-http",
                "endpoint": "/mcp",
            },

            "rag": {
                "port": 7002,
                "type": "local",
            },

            "ollama": {
                "port": 11434,
            },
        },

        "tool_architecture": {
            "feature_tools_per_feature": 5,
            "shared_tools": 5,
        },
    }