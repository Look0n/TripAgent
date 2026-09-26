"""Central registry for TripAgent MCP tool ownership and access."""


ACCOUNT_TOOLS = [
    "get_customer_profile",
    "get_customer_preferences",
    "update_customer_preferences",
    "get_customer_summary",
    "check_profile_completeness",
]

ACCOMMODATION_TOOLS = [
    "search_accommodations",
]

SHARED_TOOLS = [
    "list_tripagent_services",
    "get_service_status",
    "list_available_tools",
    "get_tripagent_help",
    "get_system_summary",
]

# Only the Account integration is registered in this release. Other feature
# teams can later add their own five tools without changing Account access.
FEATURE_TOOL_ACCESS = {
    "account": ACCOUNT_TOOLS + SHARED_TOOLS,
    "accommodation": ACCOMMODATION_TOOLS + SHARED_TOOLS,
}

TOOL_CATEGORY = {
    **{name: "account" for name in ACCOUNT_TOOLS},
    **{name: "accommodation" for name in ACCOMMODATION_TOOLS},
    **{name: "shared" for name in SHARED_TOOLS},
}


def get_tools_for_feature(feature: str) -> list[str]:
    """Return only tools explicitly available to a feature."""
    normalised_feature = str(feature or "").strip().lower()
    return FEATURE_TOOL_ACCESS.get(normalised_feature, []).copy()


def is_tool_allowed(feature: str, tool_name: str) -> bool:
    """Return True when the named feature may use the named tool."""
    return tool_name in get_tools_for_feature(feature)


def get_tool_category(tool_name: str) -> str | None:
    """Return account/shared ownership for a registered tool."""
    return TOOL_CATEGORY.get(tool_name)


def get_registry_summary() -> dict:
    """Return non-sensitive registry metadata."""
    return {
        "account_tools": ACCOUNT_TOOLS.copy(),
        "accommodation_tools": ACCOMMODATION_TOOLS.copy(),
        "shared_tools": SHARED_TOOLS.copy(),
        "feature_access": {
            feature: tools.copy()
            for feature, tools in FEATURE_TOOL_ACCESS.items()
        },
        "total_registered_tools": len(TOOL_CATEGORY),
    }
