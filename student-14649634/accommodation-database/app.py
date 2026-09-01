from flask import Flask, jsonify, request
from flask_cors import CORS

import sqlite3
import os


app = Flask(__name__)
CORS(app)


DATABASE_NAME = os.getenv(
    "DATABASE_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "accommodation.db"
    )
)


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "accommodation-database"
    })


@app.route("/accommodations", methods=["GET"])
def get_accommodations():

    city = request.args.get("city")
    accommodation_type = request.args.get("type")
    max_price = request.args.get("max_price")
    guests = request.args.get("guests")

    query = """
        SELECT *
        FROM accommodations
        WHERE 1=1
    """

    params = []


    if city:
        query += " AND LOWER(city) = LOWER(?)"
        params.append(city)


    if accommodation_type:
        query += " AND LOWER(type) = LOWER(?)"
        params.append(accommodation_type)


    if max_price is not None:
        try:
            max_price = float(max_price)
        except ValueError:
            return jsonify({
                "error": "max_price must be a number"
            }), 400

        query += " AND price_per_night <= ?"
        params.append(max_price)


    if guests is not None:
        try:
            guests = int(guests)
        except ValueError:
            return jsonify({
                "error": "guests must be an integer"
            }), 400

        query += " AND guest_capacity >= ?"
        params.append(guests)


    conn = get_db_connection()

    accommodations = conn.execute(
        query,
        params
    ).fetchall()

    conn.close()


    return jsonify([
        dict(accommodation)
        for accommodation in accommodations
    ])


@app.route(
    "/accommodations/<int:accommodation_id>",
    methods=["GET"]
)
def get_accommodation(accommodation_id):

    conn = get_db_connection()

    accommodation = conn.execute(
        """
        SELECT *
        FROM accommodations
        WHERE accommodation_id = ?
        """,
        (accommodation_id,)
    ).fetchone()

    conn.close()


    if accommodation is None:
        return jsonify({
            "error": "Accommodation not found"
        }), 404


    return jsonify(dict(accommodation))


@app.route("/accommodations", methods=["POST"])
def create_accommodation():

    data = request.get_json()

    required_fields = [
        "accommodation_name",
        "type",
        "city",
        "price_per_night",
        "guest_capacity"
    ]


    for field in required_fields:
        if field not in data:
            return jsonify({
                "error": f"Missing required field: {field}"
            }), 400


    conn = get_db_connection()

    cursor = conn.execute(
        """
        INSERT INTO accommodations (
            accommodation_name,
            type,
            city,
            address,
            price_per_night,
            guest_capacity,
            rating,
            description,
            image_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["accommodation_name"],
            data["type"],
            data["city"],
            data.get("address"),
            data["price_per_night"],
            data["guest_capacity"],
            data.get("rating"),
            data.get("description"),
            data.get("image_url")
        )
    )

    conn.commit()

    new_id = cursor.lastrowid

    accommodation = conn.execute(
        """
        SELECT *
        FROM accommodations
        WHERE accommodation_id = ?
        """,
        (new_id,)
    ).fetchone()

    conn.close()


    return jsonify(
        dict(accommodation)
    ), 201


@app.route(
    "/accommodations/<int:accommodation_id>",
    methods=["PUT"]
)
def update_accommodation(accommodation_id):

    data = request.get_json()

    conn = get_db_connection()

    accommodation = conn.execute(
        """
        SELECT *
        FROM accommodations
        WHERE accommodation_id = ?
        """,
        (accommodation_id,)
    ).fetchone()


    if accommodation is None:
        conn.close()

        return jsonify({
            "error": "Accommodation not found"
        }), 404


    conn.execute(
        """
        UPDATE accommodations
        SET accommodation_name = ?,
            type = ?,
            city = ?,
            address = ?,
            price_per_night = ?,
            guest_capacity = ?,
            rating = ?,
            description = ?,
            image_url = ?
        WHERE accommodation_id = ?
        """,
        (
            data.get(
                "accommodation_name",
                accommodation["accommodation_name"]
            ),
            data.get(
                "type",
                accommodation["type"]
            ),
            data.get(
                "city",
                accommodation["city"]
            ),
            data.get(
                "address",
                accommodation["address"]
            ),
            data.get(
                "price_per_night",
                accommodation["price_per_night"]
            ),
            data.get(
                "guest_capacity",
                accommodation["guest_capacity"]
            ),
            data.get(
                "rating",
                accommodation["rating"]
            ),
            data.get(
                "description",
                accommodation["description"]
            ),
            data.get(
                "image_url",
                accommodation["image_url"]
            ),
            accommodation_id
        )
    )

    conn.commit()


    updated = conn.execute(
        """
        SELECT *
        FROM accommodations
        WHERE accommodation_id = ?
        """,
        (accommodation_id,)
    ).fetchone()

    conn.close()


    return jsonify(dict(updated))


@app.route(
    "/accommodations/<int:accommodation_id>",
    methods=["DELETE"]
)
def delete_accommodation(accommodation_id):

    conn = get_db_connection()

    accommodation = conn.execute(
        """
        SELECT *
        FROM accommodations
        WHERE accommodation_id = ?
        """,
        (accommodation_id,)
    ).fetchone()


    if accommodation is None:
        conn.close()

        return jsonify({
            "error": "Accommodation not found"
        }), 404


    conn.execute(
        """
        DELETE FROM accommodations
        WHERE accommodation_id = ?
        """,
        (accommodation_id,)
    )

    conn.commit()
    conn.close()


    return jsonify({
        "message":
            "Accommodation deleted successfully"
    })

def initialise_database():
    conn = sqlite3.connect(DATABASE_NAME)

    with open(
        os.path.join(
            os.path.dirname(__file__),
            "schema.sql"
        ),
        "r"
    ) as schema_file:
        conn.executescript(schema_file.read())

    with open(
        os.path.join(
            os.path.dirname(__file__),
            "init.sql"
        ),
        "r"
    ) as init_file:
        conn.executescript(init_file.read())

    conn.commit()
    conn.close()

    print("Accommodation database initialised.")
    
    
if __name__ == "__main__":
    initialise_database()
    
    app.run(
        host="0.0.0.0",
        port=6002,
        debug=False
    )