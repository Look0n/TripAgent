import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request


BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(BASE_DIR / "checklist.db")
)

CHECKLIST_DATABASE_PORT = int(
    os.getenv("CHECKLIST_DATABASE_PORT", "6005")
)

VALID_ITEM_TYPES = {
    "task",
    "packing"
}

VALID_PRIORITIES = {
    "High",
    "Medium",
    "Low"
}

EDITABLE_FIELDS = {
    "title",
    "item_type",
    "category",
    "description",
    "priority",
    "is_completed"
}


app = Flask(__name__)


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_database():
    database_directory = os.path.dirname(DATABASE_PATH)

    if database_directory:
        os.makedirs(database_directory, exist_ok=True)

    connection = get_db_connection()

    try:
        schema_path = BASE_DIR / "schema.sql"
        init_path = BASE_DIR / "init.sql"

        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )

        record_count = connection.execute(
            "SELECT COUNT(*) FROM checklist_items"
        ).fetchone()[0]

        if record_count == 0:
            connection.executescript(
                init_path.read_text(encoding="utf-8")
            )

        connection.commit()

    finally:
        connection.close()


def normalise_completed(value):
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int) and value in (0, 1):
        return value

    return None


def validate_item_data(data, partial=False):
    errors = {}

    if not partial or "title" in data:
        title = data.get("title")

        if not isinstance(title, str) or not title.strip():
            errors["title"] = "Title is required"

    if not partial or "item_type" in data:
        item_type = data.get("item_type")

        if item_type not in VALID_ITEM_TYPES:
            errors["item_type"] = (
                "item_type must be task or packing"
            )

    for field in ("category", "description"):
        if field in data:
            value = data[field]

            if value is not None and not isinstance(value, str):
                errors[field] = f"{field} must be text or null"

    if "priority" in data:
        priority = data["priority"]

        if (
            priority is not None
            and priority not in VALID_PRIORITIES
        ):
            errors["priority"] = (
                "priority must be High, Medium, Low, or null"
            )

    if "is_completed" in data:
        if normalise_completed(data["is_completed"]) is None:
            errors["is_completed"] = (
                "is_completed must be true, false, 0, or 1"
            )

    return errors


def clean_item_data(data):
    cleaned = dict(data)

    for field in ("title", "category", "description"):
        if field in cleaned and isinstance(cleaned[field], str):
            cleaned[field] = cleaned[field].strip()

    if "is_completed" in cleaned:
        cleaned["is_completed"] = normalise_completed(
            cleaned["is_completed"]
        )

    return cleaned


@app.route("/health", methods=["GET"])
def health():
    connection = get_db_connection()

    try:
        connection.execute("SELECT 1").fetchone()

    finally:
        connection.close()

    return jsonify({
        "status": "healthy",
        "service": "checklist-database"
    }), 200


@app.route("/checklist-items", methods=["GET"])
def get_checklist_items():
    item_type = request.args.get("item_type")
    category = request.args.get("category")
    priority = request.args.get("priority")
    completed_raw = request.args.get("is_completed")

    if item_type and item_type not in VALID_ITEM_TYPES:
        return jsonify({
            "error": "item_type must be task or packing"
        }), 400

    if priority and priority not in VALID_PRIORITIES:
        return jsonify({
            "error": "priority must be High, Medium, or Low"
        }), 400

    completed = None

    if completed_raw is not None:
        completed_values = {
            "0": 0,
            "1": 1,
            "false": 0,
            "true": 1
        }

        completed = completed_values.get(
            completed_raw.strip().lower()
        )

        if completed is None:
            return jsonify({
                "error": (
                    "is_completed must be true, false, 0, or 1"
                )
            }), 400

    query = "SELECT * FROM checklist_items WHERE 1 = 1"
    parameters = []

    if item_type:
        query += " AND item_type = ?"
        parameters.append(item_type)

    if category:
        query += " AND LOWER(category) = LOWER(?)"
        parameters.append(category.strip())

    if priority:
        query += " AND priority = ?"
        parameters.append(priority)

    if completed is not None:
        query += " AND is_completed = ?"
        parameters.append(completed)

    query += " ORDER BY item_id ASC"

    connection = get_db_connection()

    try:
        items = connection.execute(
            query,
            parameters
        ).fetchall()

    finally:
        connection.close()

    return jsonify([
        dict(item)
        for item in items
    ]), 200


@app.route(
    "/checklist-items/<int:item_id>",
    methods=["GET"]
)
def get_checklist_item(item_id):
    connection = get_db_connection()

    try:
        item = connection.execute(
            """
            SELECT *
            FROM checklist_items
            WHERE item_id = ?
            """,
            (item_id,)
        ).fetchone()

    finally:
        connection.close()

    if item is None:
        return jsonify({
            "error": "Checklist item not found"
        }), 404

    return jsonify(dict(item)), 200


@app.route("/checklist-items", methods=["POST"])
def create_checklist_item():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A JSON object is required"
        }), 400

    unknown_fields = set(data) - EDITABLE_FIELDS

    if unknown_fields:
        return jsonify({
            "error": "Unknown fields",
            "fields": sorted(unknown_fields)
        }), 400

    errors = validate_item_data(data)

    if errors:
        return jsonify({
            "error": "Invalid checklist item",
            "fields": errors
        }), 400

    cleaned = clean_item_data(data)

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO checklist_items (
                title,
                item_type,
                category,
                description,
                priority,
                is_completed
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                cleaned["title"],
                cleaned["item_type"],
                cleaned.get("category"),
                cleaned.get("description"),
                cleaned.get("priority"),
                cleaned.get("is_completed", 0)
            )
        )

        connection.commit()

        item = connection.execute(
            """
            SELECT *
            FROM checklist_items
            WHERE item_id = ?
            """,
            (cursor.lastrowid,)
        ).fetchone()

    finally:
        connection.close()

    return jsonify(dict(item)), 201


@app.route(
    "/checklist-items/<int:item_id>",
    methods=["PUT"]
)
def update_checklist_item(item_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({
            "error": "A non-empty JSON object is required"
        }), 400

    unknown_fields = set(data) - EDITABLE_FIELDS

    if unknown_fields:
        return jsonify({
            "error": "Unknown fields",
            "fields": sorted(unknown_fields)
        }), 400

    errors = validate_item_data(data, partial=True)

    if errors:
        return jsonify({
            "error": "Invalid checklist item",
            "fields": errors
        }), 400

    cleaned = clean_item_data(data)

    connection = get_db_connection()

    try:
        existing = connection.execute(
            """
            SELECT *
            FROM checklist_items
            WHERE item_id = ?
            """,
            (item_id,)
        ).fetchone()

        if existing is None:
            return jsonify({
                "error": "Checklist item not found"
            }), 404

        updated_values = {
            field: cleaned.get(field, existing[field])
            for field in EDITABLE_FIELDS
        }

        connection.execute(
            """
            UPDATE checklist_items
            SET title = ?,
                item_type = ?,
                category = ?,
                description = ?,
                priority = ?,
                is_completed = ?
            WHERE item_id = ?
            """,
            (
                updated_values["title"],
                updated_values["item_type"],
                updated_values["category"],
                updated_values["description"],
                updated_values["priority"],
                updated_values["is_completed"],
                item_id
            )
        )

        connection.commit()

        updated_item = connection.execute(
            """
            SELECT *
            FROM checklist_items
            WHERE item_id = ?
            """,
            (item_id,)
        ).fetchone()

    finally:
        connection.close()

    return jsonify(dict(updated_item)), 200


@app.route(
    "/checklist-items/<int:item_id>",
    methods=["DELETE"]
)
def delete_checklist_item(item_id):
    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM checklist_items
            WHERE item_id = ?
            """,
            (item_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Checklist item not found"
            }), 404

        connection.commit()

    finally:
        connection.close()

    return jsonify({
        "message": "Checklist item deleted successfully"
    }), 200


if __name__ == "__main__":
    initialise_database()

    app.run(
        host="0.0.0.0",
        port=CHECKLIST_DATABASE_PORT,
        debug=False
    )
