from mcp.server.fastmcp import FastMCP

from tool_registry import ACCOUNT_TOOLS, ACCOMMODATION_TOOLS, SHARED_TOOLS
from tools.account_tools import (
    check_profile_completeness as check_profile_completeness_impl,
    get_customer_preferences as get_customer_preferences_impl,
    get_customer_profile as get_customer_profile_impl,
    get_customer_summary as get_customer_summary_impl,
    update_customer_preferences as update_customer_preferences_impl,
)

from tools.accommodation_tools import (
    search_accommodations as search_accommodations_impl,
)

from tools.tripagent_tools import (
    get_service_status as get_service_status_impl,
    get_system_summary as get_system_summary_impl,
    get_tripagent_help as get_tripagent_help_impl,
    list_available_tools as list_available_tools_impl,
    list_tripagent_services as list_tripagent_services_impl,
)


mcp = FastMCP(
    "TripAgent Shared MCP",
    host="0.0.0.0",
    port=7001,
)


# ---------------------------------------------------------------------------
# Account feature tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_customer_profile(customer_id: int) -> dict:
    """Retrieve a TripAgent customer's profile."""
    return get_customer_profile_impl(customer_id)


@mcp.tool()
def get_customer_preferences(customer_id: int) -> dict:
    """Retrieve a customer's saved travel preferences."""
    return get_customer_preferences_impl(customer_id)


@mcp.tool()
def update_customer_preferences(
    customer_id: int,
    preferences: dict,
) -> dict:
    """Update supported travel preference fields for a customer."""
    return update_customer_preferences_impl(
        customer_id,
        preferences,
    )


@mcp.tool()
def get_customer_summary(customer_id: int) -> dict:
    """Return customer profile and preferences as combined AI context."""
    return get_customer_summary_impl(customer_id)


@mcp.tool()
def check_profile_completeness(customer_id: int) -> dict:
    """Report missing required profile and travel preference fields."""
    return check_profile_completeness_impl(customer_id)


# ---------------------------------------------------------------------------
# Accommodation feature tools
# ---------------------------------------------------------------------------

@mcp.tool()
def search_accommodations(
    city: str,
    max_price: float | None = None,
    guests: int | None = None,
) -> dict:
    """Search TripAgent accommodation records."""
    return search_accommodations_impl(
        city=city,
        max_price=max_price,
        guests=guests,
    )
    

# ---------------------------------------------------------------------------
# Shared TripAgent tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_tripagent_services() -> dict:
    """List the five feature services in the current TripAgent project."""
    return list_tripagent_services_impl()


@mcp.tool()
def get_service_status(service_name: str) -> dict:
    """Check the health of a TripAgent feature backend."""
    return get_service_status_impl(service_name)


@mcp.tool()
def list_available_tools(feature: str = "account") -> dict:
    """List tools registered for a TripAgent feature."""
    return list_available_tools_impl(feature)


@mcp.tool()
def get_tripagent_help(topic: str = "general") -> dict:
    """Return help about TripAgent, Account, MCP or RAG."""
    return get_tripagent_help_impl(topic)


@mcp.tool()
def get_system_summary() -> dict:
    """Return non-sensitive TripAgent architecture information."""
    return get_system_summary_impl()


if __name__ == "__main__":
    print("=" * 60)
    print("TripAgent Shared MCP Server")
    print("=" * 60)
    print("Server status: STARTING")
    print("Transport: Streamable HTTP")
    print("Endpoint: http://localhost:7001/mcp")

    print("\nAccount tools:")
    for tool_name in ACCOUNT_TOOLS:
        print(f"- {tool_name}")
        
    print("\nAccommodation tools:")
    for tool_name in ACCOMMODATION_TOOLS:
        print(f"- {tool_name}")

    print("\nShared TripAgent tools:")
    for tool_name in SHARED_TOOLS:
        print(f"- {tool_name}")

    print(
        f"\nTotal registered tools: "
        f"{len(ACCOUNT_TOOLS) + len(ACCOMMODATION_TOOLS) + len(SHARED_TOOLS)}"
    )
    print("=" * 60)

    mcp.run(transport="streamable-http")
