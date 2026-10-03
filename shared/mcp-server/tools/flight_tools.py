from services.flight_client import (
    get_flight_by_id,
    get_flights,
    get_flights_by_route,
)


LOW_SEAT_THRESHOLD = 10

FEATURE = "flight"


def _error(tool: str, message: str) -> dict:
    return {
        "status": "error",
        "feature": FEATURE,
        "tool": tool,
        "error": message,
    }


def _clean_code(value) -> str:
    return str(value or "").strip().upper()


def _validate_flight_id(
    tool: str,
    flight_id,
) -> tuple[int | None, dict | None]:
    try:
        flight_id = int(flight_id)
    except (TypeError, ValueError):
        return None, _error(
            tool,
            "flight_id must be an integer",
        )

    if flight_id < 1:
        return None, _error(
            tool,
            "flight_id must be positive",
        )

    return flight_id, None


def search_flights_impl(
    origin: str,
    destination: str | None = None,
    max_price: float | None = None,
) -> dict:
    """
    Search flight records using structured filters.
    """

    tool = "search_flights"

    origin = _clean_code(origin)

    if not origin:
        return _error(tool, "origin is required")

    destination = _clean_code(destination) or None

    if max_price is not None:
        try:
            max_price = float(max_price)
        except (TypeError, ValueError):
            return _error(
                tool,
                "max_price must be a number",
            )

        if max_price < 0:
            return _error(
                tool,
                "max_price must be 0 or greater",
            )

    flights = get_flights(
        origin=origin,
        destination=destination,
    )

    if max_price is not None:
        flights = [
            flight
            for flight in flights
            if flight.get("price") is not None
            and float(flight["price"]) <= max_price
        ]

    return {
        "status": "success",
        "feature": FEATURE,
        "tool": tool,
        "input": {
            "origin": origin,
            "destination": destination,
            "max_price": max_price,
        },
        "count": len(flights),
        "results": flights,
    }


def get_flight_impl(
    flight_id: int,
) -> dict:
    """
    Return one flight record by identifier.
    """

    tool = "get_flight"

    flight_id, error = _validate_flight_id(
        tool,
        flight_id,
    )

    if error:
        return error

    flight = get_flight_by_id(flight_id)

    if flight is None:
        return {
            "status": "not_found",
            "feature": FEATURE,
            "tool": tool,
            "input": {
                "flight_id": flight_id,
            },
            "result": None,
            "message": "No flight exists with that identifier",
        }

    return {
        "status": "success",
        "feature": FEATURE,
        "tool": tool,
        "input": {
            "flight_id": flight_id,
        },
        "result": flight,
    }


def get_flights_by_route_impl(
    origin: str,
    destination: str,
) -> dict:
    """
    Return every flight on one route.
    """

    tool = "get_flights_by_route"

    origin = _clean_code(origin)
    destination = _clean_code(destination)

    if not origin or not destination:
        return _error(
            tool,
            "origin and destination are required",
        )

    flights = get_flights_by_route(
        origin,
        destination,
    )

    return {
        "status": "success",
        "feature": FEATURE,
        "tool": tool,
        "input": {
            "origin": origin,
            "destination": destination,
        },
        "count": len(flights),
        "results": flights,
    }


def get_cheapest_flight_impl(
    origin: str,
    destination: str,
) -> dict:
    """
    Return the lowest priced flight on one route.
    """

    tool = "get_cheapest_flight"

    origin = _clean_code(origin)
    destination = _clean_code(destination)

    if not origin or not destination:
        return _error(
            tool,
            "origin and destination are required",
        )

    flights = get_flights_by_route(
        origin,
        destination,
    )

    priced = [
        flight
        for flight in flights
        if flight.get("price") is not None
    ]

    if not priced:
        return {
            "status": "not_found",
            "feature": FEATURE,
            "tool": tool,
            "input": {
                "origin": origin,
                "destination": destination,
            },
            "result": None,
            "message": "No priced flights were found on that route",
        }

    cheapest = min(
        priced,
        key=lambda flight: float(flight["price"]),
    )

    return {
        "status": "success",
        "feature": FEATURE,
        "tool": tool,
        "input": {
            "origin": origin,
            "destination": destination,
        },
        "candidates_considered": len(priced),
        "result": cheapest,
    }


def check_seat_availability_impl(
    flight_id: int,
) -> dict:
    """
    Report remaining seats and limited availability status.
    """

    tool = "check_seat_availability"

    flight_id, error = _validate_flight_id(
        tool,
        flight_id,
    )

    if error:
        return error

    flight = get_flight_by_id(flight_id)

    if flight is None:
        return {
            "status": "not_found",
            "feature": FEATURE,
            "tool": tool,
            "input": {
                "flight_id": flight_id,
            },
            "result": None,
            "message": "No flight exists with that identifier",
        }

    seats = flight.get("seat_availability")

    if seats is None:
        return {
            "status": "unknown",
            "feature": FEATURE,
            "tool": tool,
            "input": {
                "flight_id": flight_id,
            },
            "result": {
                "flight_id": flight_id,
                "airline": flight.get("airline"),
                "seats_available": None,
                "limited_availability": None,
            },
            "message": "Seat availability is not recorded for this flight",
        }

    seats = int(seats)

    return {
        "status": "success",
        "feature": FEATURE,
        "tool": tool,
        "input": {
            "flight_id": flight_id,
        },
        "result": {
            "flight_id": flight_id,
            "airline": flight.get("airline"),
            "origin": flight.get("origin"),
            "destination": flight.get("destination"),
            "seats_available": seats,
            "limited_availability": seats < LOW_SEAT_THRESHOLD,
            "threshold": LOW_SEAT_THRESHOLD,
        },
    }
