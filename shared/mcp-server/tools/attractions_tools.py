# MCP tool implementations for the Attractions feature.
# Each function validates input, calls the HTTP client, and returns
# a consistent {status, feature, tool, input, results} shape.

from services.attractions_client import (
    get_attractions,
    get_attractions_by_city,
    search_attractions,
    get_attraction_details,
    get_top_rated_attractions,
)


def get_attractions_impl() -> dict:
    """
    Return all attraction records.
    """

    attractions = get_attractions()

    return {
        "status": "success",
        "feature": "attractions",
        "tool": "get_attractions",
        "input": {},
        "count": len(attractions),
        "results": attractions,
    }


def get_attractions_by_city_impl(
    city: str,
) -> dict:
    """
    Return attraction records for one city.
    """

    city = str(city or "").strip()

    if not city:
        return {
            "status": "error",
            "feature": "attractions",
            "tool": "get_attractions_by_city",
            "error": "city is required",
        }

    attractions = get_attractions_by_city(
        city
    )

    return {
        "status": "success",
        "feature": "attractions",
        "tool": "get_attractions_by_city",
        "input": {
            "city": city,
        },
        "count": len(attractions),
        "results": attractions,
    }


def search_attractions_impl(
    city: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
) -> dict:
    """
    Search attractions using structured filters.
    """

    if city is not None:
        city = str(city).strip() or None

    if category is not None:
        category = str(category).strip() or None

    if max_price is not None:
        try:
            max_price = float(max_price)
        except (TypeError, ValueError):
            return {
                "status": "error",
                "feature": "attractions",
                "tool": "search_attractions",
                "error": "max_price must be a number",
            }

        if max_price < 0:
            return {
                "status": "error",
                "feature": "attractions",
                "tool": "search_attractions",
                "error": "max_price must be 0 or greater",
            }

    attractions = search_attractions(
        city=city,
        category=category,
        max_price=max_price,
    )

    return {
        "status": "success",
        "feature": "attractions",
        "tool": "search_attractions",
        "input": {
            "city": city,
            "category": category,
            "max_price": max_price,
        },
        "count": len(attractions),
        "results": attractions,
    }


def get_attraction_details_impl(
    attraction_id: int,
) -> dict:
    """
    Return one attraction record including its reviews.
    """

    try:
        attraction_id = int(attraction_id)
    except (TypeError, ValueError):
        return {
            "status": "error",
            "feature": "attractions",
            "tool": "get_attraction_details",
            "error": "attraction_id must be an integer",
        }

    if attraction_id < 1:
        return {
            "status": "error",
            "feature": "attractions",
            "tool": "get_attraction_details",
            "error": "attraction_id must be positive",
        }

    try:
        attraction = get_attraction_details(
            attraction_id
        )
    except Exception as exc:
        return {
            "status": "error",
            "feature": "attractions",
            "tool": "get_attraction_details",
            "error": str(exc),
        }

    return {
        "status": "success",
        "feature": "attractions",
        "tool": "get_attraction_details",
        "input": {
            "attraction_id": attraction_id,
        },
        "result": attraction,
    }


def get_top_rated_attractions_impl(
    city: str | None = None,
    limit: int = 5,
) -> dict:
    """
    Return the highest-rated attractions, optionally filtered by city.
    """

    if city is not None:
        city = str(city).strip() or None

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return {
            "status": "error",
            "feature": "attractions",
            "tool": "get_top_rated_attractions",
            "error": "limit must be an integer",
        }

    if limit < 1:
        return {
            "status": "error",
            "feature": "attractions",
            "tool": "get_top_rated_attractions",
            "error": "limit must be at least 1",
        }

    attractions = get_top_rated_attractions(
        city=city,
        limit=limit,
    )

    return {
        "status": "success",
        "feature": "attractions",
        "tool": "get_top_rated_attractions",
        "input": {
            "city": city,
            "limit": limit,
        },
        "count": len(attractions),
        "results": attractions,
    }
