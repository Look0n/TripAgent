from mcp.server.fastmcp import FastMCP

from tool_registry import (
    ACCOUNT_TOOLS,
    CHECKLIST_TOOLS,
    ACCOMMODATION_TOOLS,
    FLIGHT_TOOLS,
    ATTRACTIONS_TOOLS,
    SHARED_TOOLS,
)
from tools.account_tools import (
    check_profile_completeness as check_profile_completeness_impl,
    get_customer_preferences as get_customer_preferences_impl,
    get_customer_profile as get_customer_profile_impl,
    get_customer_summary as get_customer_summary_impl,
    update_customer_preferences as update_customer_preferences_impl,
)

from tools.accommodation_tools import (
    search_accommodations as search_accommodations_impl,
    get_accommodations as get_accommodations_impl,
    get_accommodation_by_city as get_accommodation_by_city_impl,
    check_accommodation_availability as check_accommodation_availability_impl,
)

from tools.flight_tools import (
    check_seat_availability_impl,
    get_cheapest_flight_impl,
    get_flight_impl,
    get_flights_by_route_impl,
    search_flights_impl,
)

from tools.attractions_tools import (
    get_attractions_impl as get_attractions_impl,
    get_attractions_by_city_impl as get_attractions_by_city_impl,
    search_attractions_impl as search_attractions_impl,
    get_attraction_details_impl as get_attraction_details_impl,
    get_top_rated_attractions_impl as get_top_rated_attractions_impl,
)

from tools.checklist_tools import (
    get_checklist_item as get_checklist_item_impl,
    get_checklist_items as get_checklist_items_impl,
    get_checklist_summary as get_checklist_summary_impl,
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
def get_accommodations() -> dict:
    return get_accommodations_impl()


@mcp.tool()
def get_accommodation_by_city(
    city: str,
) -> dict:
    return get_accommodation_by_city_impl(
        city
    )
    
    
@mcp.tool()
def search_accommodations(
    city: str,
    max_price: float | None = None,
    guests: int | None = None,
    type: str | None = None,
) -> dict:
    """Search TripAgent accommodation records."""
    return search_accommodations_impl(
        city=city,
        max_price=max_price,
        guests=guests,
        type=type,
    )
    
    
@mcp.tool()
def check_accommodation_availability(
    accommodation_id: int,
    check_in: str,
    check_out: str,
) -> dict:
    return check_accommodation_availability_impl(
        accommodation_id,
        check_in,
        check_out,
    )
    

# ---------------------------------------------------------------------------
# Flight feature tools
# ---------------------------------------------------------------------------

@mcp.tool()
def search_flights(
    origin: str,
    destination: str | None = None,
    max_price: float | None = None,
) -> dict:
    """Search TripAgent flight records by route and optional maximum price."""
    return search_flights_impl(
        origin=origin,
        destination=destination,
        max_price=max_price,
    )


@mcp.tool()
def get_flight(flight_id: int) -> dict:
    """Retrieve one flight record by its identifier."""
    return get_flight_impl(flight_id)


@mcp.tool()
def get_flights_by_route(
    origin: str,
    destination: str,
) -> dict:
    """List every flight between two airports."""
    return get_flights_by_route_impl(
        origin,
        destination,
    )


@mcp.tool()
def get_cheapest_flight(
    origin: str,
    destination: str,
) -> dict:
    """Return the lowest priced flight on a route."""
    return get_cheapest_flight_impl(
        origin,
        destination,
    )


@mcp.tool()
def check_seat_availability(flight_id: int) -> dict:
    """Report remaining seats and limited availability for one flight."""
    return check_seat_availability_impl(flight_id)


# ---------------------------------------------------------------------------
# Attractions feature tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_attractions() -> dict:
    """Return all attraction and tour records."""
    return get_attractions_impl()


@mcp.tool()
def get_attractions_by_city(
    city: str,
) -> dict:
    """Return attraction records for one city."""
    return get_attractions_by_city_impl(
        city
    )


@mcp.tool()
def search_attractions(
    city: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
) -> dict:
    """Search TripAgent attraction records by city, category and price."""
    return search_attractions_impl(
        city=city,
        category=category,
        max_price=max_price,
    )


@mcp.tool()
def get_attraction_details(
    attraction_id: int,
) -> dict:
    """Return one attraction record including its customer reviews."""
    return get_attraction_details_impl(
        attraction_id
    )


@mcp.tool()
def get_top_rated_attractions(
    city: str | None = None,
    limit: int = 5,
) -> dict:
    """Return the highest-rated attractions, optionally filtered by city."""
    return get_top_rated_attractions_impl(
        city=city,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Checklist feature tools
# ---------------------------------------------------------------------------
@mcp.tool()
def get_checklist_items(
    item_type: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    is_completed: bool | None = None,
) -> dict:
    return get_checklist_items_impl(
        item_type=item_type,
        category=category,
        priority=priority,
        is_completed=is_completed,
    )

@mcp.tool()
def get_checklist_item(item_id: int) -> dict:
    return get_checklist_item_impl(item_id)

@mcp.tool()
def get_checklist_summary() -> dict:
    return get_checklist_summary_impl()

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

    print("\nFlight tools:")
    for tool_name in FLIGHT_TOOLS:
        print(f"- {tool_name}")

    print("\nAttractions tools:")
    for tool_name in ATTRACTIONS_TOOLS:
        print(f"- {tool_name}")

    print("\nChecklist tools:")
    for tool_name in CHECKLIST_TOOLS:
        print(f"- {tool_name}")

    print("\nShared TripAgent tools:")
    for tool_name in SHARED_TOOLS:
        print(f"- {tool_name}")

    total_tools = (
        len(ACCOUNT_TOOLS)
        + len(ACCOMMODATION_TOOLS)
        + len(FLIGHT_TOOLS)
        + len(ATTRACTIONS_TOOLS)
        + len(CHECKLIST_TOOLS)
        + len(SHARED_TOOLS)
    )

    print(f"\nTotal registered tools: {total_tools}")
    print("=" * 60)

    mcp.run(transport="streamable-http")
