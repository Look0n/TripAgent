from services.accommodation_client import (
    search_accommodations as search_accommodations_api,
)


def search_accommodations(
    city: str,
    max_price: float | None = None,
    guests: int | None = None,
) -> dict:
    """
    Search TripAgent accommodation records.

    Boundary:
    - Read-only.
    - Accommodation feature only.
    - Does not directly access SQLite.
    - Does not create, update, or delete records.
    """

    city = str(city or "").strip()

    if not city:
        return {
            "status": "error",
            "error": "city_required",
        }

    if max_price is not None and max_price < 0:
        return {
            "status": "error",
            "error": "invalid_max_price",
        }

    if guests is not None and guests <= 0:
        return {
            "status": "error",
            "error": "invalid_guests",
        }

    try:
        results = search_accommodations_api(
            city=city,
            max_price=max_price,
            guests=guests,
        )

        return {
            "status": "success",
            "feature": "accommodation",
            "tool": "search_accommodations",
            "input": {
                "city": city,
                "max_price": max_price,
                "guests": guests,
            },
            "count": len(results),
            "results": results,
        }

    except Exception as exc:
        return {
            "status": "error",
            "feature": "accommodation",
            "tool": "search_accommodations",
            "error": str(exc),
        }