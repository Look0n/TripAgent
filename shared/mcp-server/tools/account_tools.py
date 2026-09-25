"""The five MCP tools owned by the TripAgent Account feature."""

from services.account_client import (
    AccountServiceError,
    get_preferences,
    get_profile,
    update_preferences,
)


PREFERENCE_FIELDS = (
    "budget_level",
    "travel_style",
    "accommodation_type",
    "transport_preference",
    "food_preference",
    "pace_preference",
)

PROFILE_REQUIRED_FIELDS = (
    "first_name",
    "last_name",
    "email",
)


def _valid_customer_id(customer_id: int) -> bool:
    return isinstance(customer_id, int) and customer_id > 0


def get_customer_profile(customer_id: int) -> dict:
    """Retrieve the authenticated customer's Account profile."""
    if not _valid_customer_id(customer_id):
        return {
            "success": False,
            "error": "A valid customer_id is required",
        }

    try:
        return {
            "success": True,
            "customer_id": customer_id,
            "profile": get_profile(customer_id),
        }
    except AccountServiceError as exc:
        return {
            "success": False,
            "error": str(exc),
        }


def get_customer_preferences(customer_id: int) -> dict:
    """Retrieve the authenticated customer's six travel preferences."""
    if not _valid_customer_id(customer_id):
        return {
            "success": False,
            "error": "A valid customer_id is required",
        }

    try:
        return {
            "success": True,
            "customer_id": customer_id,
            "preferences": get_preferences(customer_id),
        }
    except AccountServiceError as exc:
        return {
            "success": False,
            "error": str(exc),
        }


def update_customer_preferences(
    customer_id: int,
    preferences: dict,
) -> dict:
    """Update supported preference fields for the authenticated customer."""
    if not _valid_customer_id(customer_id):
        return {
            "success": False,
            "error": "A valid customer_id is required",
        }

    if not isinstance(preferences, dict):
        return {
            "success": False,
            "error": "preferences must be an object",
        }

    clean_preferences = {
        key: value
        for key, value in preferences.items()
        if key in PREFERENCE_FIELDS
    }

    if not clean_preferences:
        return {
            "success": False,
            "error": "No supported preference fields were supplied",
            "allowed_fields": list(PREFERENCE_FIELDS),
        }

    try:
        result = update_preferences(
            customer_id,
            clean_preferences,
        )
        return {
            "success": True,
            "customer_id": customer_id,
            "updated_fields": list(clean_preferences.keys()),
            "result": result,
        }
    except AccountServiceError as exc:
        return {
            "success": False,
            "error": str(exc),
        }


def get_customer_summary(customer_id: int) -> dict:
    """Return profile and preference data together for AI context."""
    if not _valid_customer_id(customer_id):
        return {
            "success": False,
            "error": "A valid customer_id is required",
        }

    try:
        profile = get_profile(customer_id)
        preferences = get_preferences(customer_id)
        return {
            "success": True,
            "customer_id": customer_id,
            "summary": {
                "profile": profile,
                "preferences": preferences,
            },
        }
    except AccountServiceError as exc:
        return {
            "success": False,
            "error": str(exc),
        }


def check_profile_completeness(customer_id: int) -> dict:
    """Report missing required profile fields and empty preference fields."""
    if not _valid_customer_id(customer_id):
        return {
            "success": False,
            "error": "A valid customer_id is required",
        }

    try:
        profile = get_profile(customer_id)
        preferences = get_preferences(customer_id)
    except AccountServiceError as exc:
        return {
            "success": False,
            "error": str(exc),
        }

    missing_profile_fields = [
        field
        for field in PROFILE_REQUIRED_FIELDS
        if not str(profile.get(field) or "").strip()
    ]

    missing_preference_fields = [
        field
        for field in PREFERENCE_FIELDS
        if not str(preferences.get(field) or "").strip()
    ]

    missing_fields = (
        [f"profile.{field}" for field in missing_profile_fields]
        + [
            f"preferences.{field}"
            for field in missing_preference_fields
        ]
    )

    return {
        "success": True,
        "customer_id": customer_id,
        "complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "profile_complete": len(missing_profile_fields) == 0,
        "preferences_complete": len(missing_preference_fields) == 0,
    }
