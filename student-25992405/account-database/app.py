import os
import sqlite3

from flask import Flask, jsonify, request


app = Flask(__name__)

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "/data/account.db"
)


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialise_database():
    database_directory = os.path.dirname(DATABASE_PATH)

    if database_directory:
        os.makedirs(database_directory, exist_ok=True)

    connection = get_connection()

    try:
        with open("schema.sql", "r", encoding="utf-8") as file:
            connection.executescript(file.read())

        with open("init.sql", "r", encoding="utf-8") as file:
            connection.executescript(file.read())

        connection.commit()

    finally:
        connection.close()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "account-database"
    }), 200


# ---------------------------------------------------------
# CUSTOMER
# ---------------------------------------------------------

@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "first_name",
        "last_name",
        "email",
        "password"
    ]

    missing_fields = [
        field
        for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields
        }), 400

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO customer (
                first_name,
                last_name,
                email,
                password,
                phone,
                country
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["first_name"].strip(),
                data["last_name"].strip(),
                data["email"].strip().lower(),
                data["password"],
                data.get("phone"),
                data.get("country")
            )
        )

        connection.commit()

        return jsonify({
            "message": "Customer created",
            "customer_id": cursor.lastrowid
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "An account with this email already exists"
        }), 409

    finally:
        connection.close()


@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    connection = get_connection()

    try:
        customer = connection.execute(
            """
            SELECT
                customer_id,
                first_name,
                last_name,
                email,
                phone,
                country,
                created_at
            FROM customer
            WHERE customer_id = ?
            """,
            (customer_id,)
        ).fetchone()

        if customer is None:
            return jsonify({
                "error": "Customer not found"
            }), 404

        return jsonify(dict(customer)), 200

    finally:
        connection.close()


@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    data = request.get_json(silent=True) or {}

    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT *
            FROM customer
            WHERE customer_id = ?
            """,
            (customer_id,)
        ).fetchone()

        if existing is None:
            return jsonify({
                "error": "Customer not found"
            }), 404

        first_name = data.get(
            "first_name",
            existing["first_name"]
        )

        last_name = data.get(
            "last_name",
            existing["last_name"]
        )

        phone = data.get(
            "phone",
            existing["phone"]
        )

        country = data.get(
            "country",
            existing["country"]
        )

        connection.execute(
            """
            UPDATE customer
            SET
                first_name = ?,
                last_name = ?,
                phone = ?,
                country = ?
            WHERE customer_id = ?
            """,
            (
                first_name,
                last_name,
                phone,
                country,
                customer_id
            )
        )

        connection.commit()

        return jsonify({
            "message": "Customer profile updated"
        }), 200

    finally:
        connection.close()


@app.route("/customers/by-email", methods=["GET"])
def get_customer_by_email():
    email = request.args.get(
        "email",
        ""
    ).strip().lower()

    if not email:
        return jsonify({
            "error": "Email is required"
        }), 400

    connection = get_connection()

    try:
        customer = connection.execute(
            """
            SELECT *
            FROM customer
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if customer is None:
            return jsonify({
                "error": "Customer not found"
            }), 404

        # Internal endpoint.
        # Password hash is required by backend login validation.
        return jsonify(dict(customer)), 200

    finally:
        connection.close()


# ---------------------------------------------------------
# PREFERENCE
# ---------------------------------------------------------

@app.route(
    "/preferences/<int:customer_id>",
    methods=["GET"]
)
def get_preference(customer_id):
    connection = get_connection()

    try:
        preference = connection.execute(
            """
            SELECT *
            FROM preference
            WHERE customer_id = ?
            """,
            (customer_id,)
        ).fetchone()

        if preference is None:
            return jsonify({
                "error": "Preference profile not found"
            }), 404

        return jsonify(dict(preference)), 200

    finally:
        connection.close()


@app.route(
    "/preferences/<int:customer_id>",
    methods=["PUT"]
)
def save_preference(customer_id):
    data = request.get_json(silent=True) or {}

    connection = get_connection()

    try:
        customer = connection.execute(
            """
            SELECT customer_id
            FROM customer
            WHERE customer_id = ?
            """,
            (customer_id,)
        ).fetchone()

        if customer is None:
            return jsonify({
                "error": "Customer not found"
            }), 404

        connection.execute(
            """
            INSERT INTO preference (
                customer_id,
                budget_level,
                travel_style,
                accommodation_type,
                transport_preference,
                food_preference,
                pace_preference
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(customer_id)
            DO UPDATE SET
                budget_level = excluded.budget_level,
                travel_style = excluded.travel_style,
                accommodation_type = excluded.accommodation_type,
                transport_preference =
                    excluded.transport_preference,
                food_preference =
                    excluded.food_preference,
                pace_preference =
                    excluded.pace_preference
            """,
            (
                customer_id,
                data.get("budget_level"),
                data.get("travel_style"),
                data.get("accommodation_type"),
                data.get("transport_preference"),
                data.get("food_preference"),
                data.get("pace_preference")
            )
        )

        connection.commit()

        return jsonify({
            "message": "Preference profile saved"
        }), 200

    finally:
        connection.close()


@app.route(
    "/preferences/<int:customer_id>",
    methods=["DELETE"]
)
def delete_preference(customer_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM preference
            WHERE customer_id = ?
            """,
            (customer_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Preference profile not found"
            }), 404

        return jsonify({
            "message": "Preference profile deleted"
        }), 200

    finally:
        connection.close()


if __name__ == "__main__":
    initialise_database()

    app.run(
        host="0.0.0.0",
        port=6001
    )