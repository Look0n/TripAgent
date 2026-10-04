import os

MCP_CASES = {
    "account": {
        "tools": ["get_customer_profile", "get_customer_preferences", "get_customer_summary", "check_profile_completeness", "update_customer_preferences"],
        "list_tool": "get_customer_profile", "arguments": {}, "object_key": "profile",
        "invalid_tool": "get_customer_profile", "invalid_arguments": {"customer_id": 0}, "error_terms": ["customer_id"],
    },
    "accommodation": {
        "tools": ["get_accommodations", "get_accommodation_by_city", "search_accommodations", "check_accommodation_availability"],
        "list_tool": "get_accommodations", "arguments": {}, "list_key": "results",
        "invalid_tool": "get_accommodation_by_city", "invalid_arguments": {"city": ""}, "error_terms": ["city"],
    },
    "attractions": {
        "tools": ["get_attractions", "get_attractions_by_city", "search_attractions", "get_attraction_details", "get_top_rated_attractions"],
        "list_tool": "get_attractions", "arguments": {}, "list_key": "results",
        "invalid_tool": "get_attractions_by_city", "invalid_arguments": {"city": ""}, "error_terms": ["city"],
    },
    "checklist": {
        "tools": ["get_checklist_items", "get_checklist_item", "get_checklist_summary"],
        "list_tool": "get_checklist_items", "arguments": {}, "list_key": "items",
        "single_tool": "get_checklist_item", "id_field": "item_id", "object_key": "item",
        "invalid_tool": "get_checklist_item", "invalid_arguments": {"item_id": 0}, "error_terms": ["positive"],
    },
    "flight": {
        "tools": ["search_flights", "get_flight", "get_flights_by_route", "get_cheapest_flight", "check_seat_availability"],
        "list_tool": "search_flights", "arguments": {"origin": os.getenv("LOOP_FLIGHT_ORIGIN", "SYD")}, "list_key": "results",
        "single_tool": "get_flight", "id_field": "flight_id", "object_key": "result",
        "invalid_tool": "get_flight", "invalid_arguments": {"flight_id": 0}, "error_terms": ["positive"],
    },
}

RAG_TOPICS = {
    "account": [("What travel preferences does Account support?", "preferences"), ("Does updating a profile require authentication?", "security"), ("Are AI preference suggestions saved automatically?", "ai")],
    "accommodation": [("Which filters can I use to search accommodation?", "filters"), ("What happens when accommodation availability is missing?", "availability"), ("What can users do in the Accommodation service?", "search")],
    "attractions": [("What attraction categories are available?", "categories"), ("How are attraction review ratings calculated?", "reviews"), ("How does the Attractions AI recommend activities?", "ai")],
    "checklist": [("What is the difference between task and packing items?", "item_types"), ("What priorities does Checklist support?", "priority"), ("When do changed checklist records appear in RAG answers?", "snapshot")],
    "flight": [("When is a flight reported as limited availability?", "availability"), ("What operations does Flight Search support?", "crud"), ("May flight recommendations invent prices or airlines?", "grounding")],
}


def rag_cases(feature):
    cases = [
        {"id": f"{feature}_{topic}", "query": query, "relevant_ids": [f"{feature}_knowledge_{topic}"], "answerable": True}
        for query, topic in RAG_TOPICS[feature]
    ]
    cases.append({"id": f"{feature}_unsupported", "query": "What is the exact surface temperature of the fictional planet Zorblax-99?", "relevant_ids": [], "answerable": False})
    return cases
