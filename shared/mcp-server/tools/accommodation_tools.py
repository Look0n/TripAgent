from services.accommodation_client import (
    get_accommodations,
    get_accommodation_by_city,
    search_accommodations,
    check_accommodation_availability,
)


def get_accommodations_impl() -> dict:
    """
    Return all accommodation records.
    """

    accommodations = get_accommodations()

    return {
        "status": "success",
        "feature": "accommodation",
        "tool": "get_accommodations",
        "input": {},
        "count": len(accommodations),
        "results": accommodations,
    }


def get_accommodation_by_city_impl(
    city: str,
) -> dict:
    """
    Return accommodation records for one city.
    """

    city = str(city or "").strip()

    if not city:
        return {
            "status": "error",
            "feature": "accommodation",
            "tool": "get_accommodation_by_city",
            "error": "city is required",
        }

    accommodations = get_accommodation_by_city(
        city
    )

    return {
        "status": "success",
        "feature": "accommodation",
        "tool": "get_accommodation_by_city",
        "input": {
            "city": city,
        },
        "count": len(accommodations),
        "results": accommodations,
    }


def search_accommodations_impl(
    city: str,
    max_price: float | None = None,
    guests: int | None = None,
    type: str | None = None,
) -> dict:
    """
    Search accommodations using structured filters.
    """

    city = str(city or "").strip()

    if not city:
        return {
            "status": "error",
            "feature": "accommodation",
            "tool": "search_accommodations",
            "error": "city is required",
        }

    if max_price is not None:
        try:
            max_price = float(max_price)
        except (TypeError, ValueError):
            return {
                "status": "error",
                "feature": "accommodation",
                "tool": "search_accommodations",
                "error": "max_price must be a number",
            }

        if max_price < 0:
            return {
                "status": "error",
                "feature": "accommodation",
                "tool": "search_accommodations",
                "error": "max_price must be 0 or greater",
            }

    if guests is not None:
        try:
            guests = int(guests)
        except (TypeError, ValueError):
            return {
                "status": "error",
                "feature": "accommodation",
                "tool": "search_accommodations",
                "error": "guests must be an integer",
            }

        if guests < 1:
            return {
                "status": "error",
                "feature": "accommodation",
                "tool": "search_accommodations",
                "error": "guests must be at least 1",
            }

    if type is not None:
        type = str(
            type
        ).strip()

        if not type:
            type = None

    accommodations = search_accommodations(
        city=city,
        max_price=max_price,
        guests=guests,
        type=type,
    )

    return {
        "status": "success",
        "feature": "accommodation",
        "tool": "search_accommodations",
        "input": {
            "city": city,
            "max_price": max_price,
            "guests": guests,
            "type": type,
        },
        "count": len(accommodations),
        "results": accommodations,
    }


def check_accommodation_availability_impl(
    accommodation_id: int,
    check_in: str,
    check_out: str,
) -> dict:
    """
    Check availability for one accommodation
    between two dates.
    """

    try:
        accommodation_id = int(
            accommodation_id
        )
    except (TypeError, ValueError):
        return {
            "status": "error",
            "feature": "accommodation",
            "tool":
                "check_accommodation_availability",
            "error":
                "accommodation_id must be an integer",
        }

    if accommodation_id < 1:
        return {
            "status": "error",
            "feature": "accommodation",
            "tool":
                "check_accommodation_availability",
            "error":
                "accommodation_id must be positive",
        }

    check_in = str(check_in or "").strip()
    check_out = str(check_out or "").strip()

    if not check_in or not check_out:
        return {
            "status": "error",
            "feature": "accommodation",
            "tool":
                "check_accommodation_availability",
            "error":
                "check_in and check_out are required",
        }

    availability = (
        check_accommodation_availability(
            accommodation_id=accommodation_id,
            check_in=check_in,
            check_out=check_out,
        )
    )

    return {
        "status": "success",
        "feature": "accommodation",
        "tool":
            "check_accommodation_availability",
        "input": {
            "accommodation_id":
                accommodation_id,
            "check_in": check_in,
            "check_out": check_out,
        },
        "result": availability,
    }