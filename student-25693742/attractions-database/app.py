import os
import sqlite3

from flask import Flask, jsonify, request
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "/data/attractions.db"
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
        "service": "attractions-database"
    }), 200


# ---------------------------------------------------------
# ATTRACTIONS
# ---------------------------------------------------------

@app.route("/attractions", methods=["GET"])
def get_attractions():
    search_query = request.args.get("search", "").strip()
    city = request.args.get("city")
    category = request.args.get("category")
    max_price = request.args.get("max_price")

    query = "SELECT * FROM attractions WHERE 1=1"
    params = []

    if search_query:
        query += (
            " AND (name LIKE ? OR city LIKE ?"
            " OR description LIKE ? OR category LIKE ?)"
        )
        like_param = f"%{search_query}%"
        params.extend([like_param, like_param, like_param, like_param])

    if city:
        query += " AND LOWER(city) = LOWER(?)"
        params.append(city)

    if category:
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)

    if max_price is not None:
        try:
            max_price = float(max_price)
        except ValueError:
            return jsonify({
                "error": "max_price must be a number"
            }), 400

        query += " AND price <= ?"
        params.append(max_price)

    connection = get_connection()
    rows = connection.execute(query, params).fetchall()
    connection.close()

    return jsonify([dict(row) for row in rows])


@app.route("/attractions/<int:attraction_id>", methods=["GET"])
def get_attraction(attraction_id):
    connection = get_connection()

    attraction = connection.execute(
        "SELECT * FROM attractions WHERE attraction_id = ?",
        (attraction_id,)
    ).fetchone()

    if attraction is None:
        connection.close()
        return jsonify({"error": "Attraction not found"}), 404

    reviews = connection.execute(
        "SELECT * FROM reviews WHERE attraction_id = ? ORDER BY created_at DESC",
        (attraction_id,)
    ).fetchall()

    connection.close()

    result = dict(attraction)
    result["reviews"] = [dict(review) for review in reviews]

    return jsonify(result)


@app.route("/attractions", methods=["POST"])
def create_attraction():
    data = request.get_json(silent=True) or {}

    required_fields = ["name", "category", "city", "price"]

    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO attractions (
            name, category, city, price,
            image_url, description, average_rating
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["name"],
            data["category"],
            data["city"],
            data["price"],
            data.get("image_url"),
            data.get("description"),
            data.get("average_rating", 0.0)
        )
    )

    connection.commit()

    new_id = cursor.lastrowid

    attraction = connection.execute(
        "SELECT * FROM attractions WHERE attraction_id = ?",
        (new_id,)
    ).fetchone()

    connection.close()

    return jsonify(dict(attraction)), 201


@app.route("/attractions/<int:attraction_id>", methods=["PUT"])
def update_attraction(attraction_id):
    data = request.get_json(silent=True) or {}

    connection = get_connection()

    attraction = connection.execute(
        "SELECT * FROM attractions WHERE attraction_id = ?",
        (attraction_id,)
    ).fetchone()

    if attraction is None:
        connection.close()
        return jsonify({"error": "Attraction not found"}), 404

    connection.execute(
        """
        UPDATE attractions
        SET name = ?,
            category = ?,
            city = ?,
            price = ?,
            image_url = ?,
            description = ?,
            average_rating = ?
        WHERE attraction_id = ?
        """,
        (
            data.get("name", attraction["name"]),
            data.get("category", attraction["category"]),
            data.get("city", attraction["city"]),
            data.get("price", attraction["price"]),
            data.get("image_url", attraction["image_url"]),
            data.get("description", attraction["description"]),
            data.get("average_rating", attraction["average_rating"]),
            attraction_id
        )
    )

    connection.commit()

    updated = connection.execute(
        "SELECT * FROM attractions WHERE attraction_id = ?",
        (attraction_id,)
    ).fetchone()

    connection.close()

    return jsonify(dict(updated))


@app.route("/attractions/<int:attraction_id>", methods=["DELETE"])
def delete_attraction(attraction_id):
    connection = get_connection()

    attraction = connection.execute(
        "SELECT * FROM attractions WHERE attraction_id = ?",
        (attraction_id,)
    ).fetchone()

    if attraction is None:
        connection.close()
        return jsonify({"error": "Attraction not found"}), 404

    connection.execute(
        "DELETE FROM reviews WHERE attraction_id = ?",
        (attraction_id,)
    )
    connection.execute(
        "DELETE FROM attractions WHERE attraction_id = ?",
        (attraction_id,)
    )

    connection.commit()
    connection.close()

    return jsonify({"message": "Attraction deleted successfully"})


# ---------------------------------------------------------
# REVIEWS
# ---------------------------------------------------------

@app.route("/attractions/<int:attraction_id>/reviews", methods=["GET"])
def get_reviews(attraction_id):
    connection = get_connection()

    reviews = connection.execute(
        "SELECT * FROM reviews WHERE attraction_id = ? ORDER BY created_at DESC",
        (attraction_id,)
    ).fetchall()

    connection.close()

    return jsonify([dict(review) for review in reviews])


@app.route("/attractions/<int:attraction_id>/reviews", methods=["POST"])
def create_review(attraction_id):
    data = request.get_json(silent=True) or {}

    if "rating" not in data:
        return jsonify({"error": "Missing required field: rating"}), 400

    connection = get_connection()

    attraction = connection.execute(
        "SELECT attraction_id FROM attractions WHERE attraction_id = ?",
        (attraction_id,)
    ).fetchone()

    if attraction is None:
        connection.close()
        return jsonify({"error": "Attraction not found"}), 404

    connection.execute(
        """
        INSERT INTO reviews (attraction_id, user_id, rating, comment)
        VALUES (?, ?, ?, ?)
        """,
        (
            attraction_id,
            data.get("user_id"),
            data["rating"],
            data.get("comment")
        )
    )

    average_rating = connection.execute(
        "SELECT AVG(rating) AS average FROM reviews WHERE attraction_id = ?",
        (attraction_id,)
    ).fetchone()["average"]

    connection.execute(
        "UPDATE attractions SET average_rating = ? WHERE attraction_id = ?",
        (round(average_rating, 1), attraction_id)
    )

    connection.commit()

    reviews = connection.execute(
        "SELECT * FROM reviews WHERE attraction_id = ? ORDER BY created_at DESC",
        (attraction_id,)
    ).fetchall()

    connection.close()

    return jsonify([dict(review) for review in reviews]), 201


if __name__ == "__main__":
    initialise_database()

    app.run(
        host="0.0.0.0",
        port=6003,
        debug=False
    )
