from services.checklist_client import (
    ChecklistServiceError,
    get_item,
    get_items,
)

VALID_ITEM_TYPES = (
    "task",
    "packing",
)

VALID_PRIORITIES = (
    "High",
    "Medium",
    "Low",
)

def get_checklist_items(
        item_type: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        is_completed: bool | None = None,
) -> dict:
    """Get checklist items using optional filters"""

    if item_type is not None and item_type not in VALID_ITEM_TYPES:
        return {
            "success": False,
            "error": f"Invalid item_type: {item_type}. item_type must be task or packing",
        }

    if priority is not None and priority not in VALID_PRIORITIES:
        return {
            "success": False,
            "error": "priority must be High, Medium, or Low",
        }

    if category is not None:
        if not isinstance(category, str) or not category.strip():
            return {
                "success": False,
                "error": "category must be a non-empty text",
            }

        category = category.strip()

    if is_completed is not None and not isinstance(is_completed, bool):
        return {
            "success": False,
            "error": "is_completed must be true or false",
        }

    params = {}

    if item_type is not None:
        params["item_type"] = item_type

    if category is not None:
        params["category"] = category

    if priority is not None:
        params["priority"] = priority

    if is_completed is not None:
        params["is_completed"] = str(is_completed).lower()

    try:
        items = get_items(params=params)

        return {
            "success": True,
            "count": len(items),
            "items": items,
        }

    except ChecklistServiceError as exc:
        return {
            "success": False,
            "error": str(exc),
        }

def get_checklist_item(
        item_id: int
) -> dict:
    """Get one checklist item using its ID"""

    if type(item_id) is not int or item_id < 1:
        return {
            "success": False,
            "error": "item_id must be a positive integer",
        }

    try:
        return{
            "success": True,
            "item": get_item(item_id),
        }

    except ChecklistServiceError as exc:
        return {
            "success": False,
            "error": str(exc),
        }

def get_checklist_summary() -> dict:
    """ Return complete counts for the whole checklist """

    try:
        items = get_items()

    except ChecklistServiceError as exc:
        return {
            "success": False,
            "error": str(exc),
        }
    
    for item in items:
        completed_value = item.get("is_completed")

        if (
            type(completed_value) not in (int, bool)
            or completed_value not in (0,1)
        ):
            return {
                "success": False,
                "error": "Checklist data contains an invalied completion value",
            }

        if item.get("priority") not in (*VALID_PRIORITIES, None):
            return {
                "success": False,
                "error": "Checklist data contains an invalid priority",
            }

    total = len(items)

    completed = sum(
        item["is_completed"] == 1
        for item in items
    )

    high_priority_pending = sum(
        item.get("priority") == "High" 
        and item["is_completed"] == 0
        for item in items
    )

    return {
        "success": True,
        "summary": {
            "total": total,
            "completed": completed,
            "pending": (total - completed),
            "high_priority_pending": high_priority_pending,
        }
    }