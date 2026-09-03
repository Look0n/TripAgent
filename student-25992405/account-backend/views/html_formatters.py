from html import escape
import re


PREFERENCE_CATEGORIES = [
    "Budget Level",
    "Travel Style",
    "Accommodation Type",
    "Transport Preference",
    "Food Preference",
    "Pace Preference",
]


def format_ai_response(text):
    if not text:
        return ""

    # Escape model output first for safety
    escaped = escape(text.strip())

    # Split before each known preference category
    pattern = (
        r"(?="
        + "|".join(
            re.escape(category) + r"\s*:"
            for category in PREFERENCE_CATEGORIES
        )
        + r")"
    )

    parts = re.split(
        pattern,
        escaped
    )

    formatted_items = []

    for part in parts:
        part = part.strip()

        if not part or ":" not in part:
            continue

        category, value = part.split(
            ":",
            1
        )

        category = category.strip()
        value = value.strip()

        if category not in PREFERENCE_CATEGORIES:
            continue

        formatted_items.append(
            f"""
            <div class="ai-preference-item">
                <strong>{category}</strong>
                <span>{value}</span>
            </div>
            """
        )

    return (
        '<div class="ai-preference-results">'
        + "".join(formatted_items)
        + "</div>"
    )