import os
import sqlite3

from flask import Flask, jsonify, request


app = Flask(__name__)

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "/data/flight.db"
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
        "service": "flight-database"
    }), 200



@app.route("/flights", methods=["GET"])
def list_flights():
    origin = request.args.get("origin")
    destination = request.args.get("destination")

    query = "SELECT * FROM flights WHERE 1=1"
    params = []

    if origin:
        query += " AND origin = ?"
        params.append(origin)

    if destination:
        query += " AND destination = ?"
        params.append(destination)

    connection = get_connection()

    try:
        rows = connection.execute(query, params).fetchall()
    finally:
        connection.close()

    return jsonify([dict(row) for row in rows]), 200


@app.route("/flights/<int:flight_id>", methods=["GET"])
def get_flight(flight_id):
    connection = get_connection()

    try:
        row = connection.execute(
            "SELECT * FROM flights WHERE flight_id = ?",
            (flight_id,)
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return jsonify({"error": "Flight not found"}), 404

    return jsonify(dict(row)), 200

@app.route("/flights", methods=["POST"])
def create_flight():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "airline",
        "origin",
        "destination",
        "departure_time",
        "arrival_time",
        "price",
        "duration",
        "seat_availability"
    ]

    missing_fields = [
        field
        for field in required_fields
        if data.get(field) is None
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
            INSERT INTO flights (
                airline,
                origin,
                destination,
                departure_time,
                arrival_time,
                price,
                duration,
                image,
                seat_availability
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["airline"],
                data["origin"],
                data["destination"],
                data["departure_time"],
                data["arrival_time"],
                data["price"],
                data["duration"],
                data.get("image"),
                data["seat_availability"]
            )
        )

        connection.commit()

        new_flight_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "A flight with this airline, route and departure time already exists"
        }), 409

    finally:
        connection.close()

    return jsonify({
        "flight_id": new_flight_id,
        "message": "Flight created"
    }), 201


@app.route("/flights/<int:flight_id>", methods=["PUT"])
def update_flight(flight_id):
    data = request.get_json(silent=True) or {}

    required_fields = [
        "airline",
        "origin",
        "destination",
        "departure_time",
        "arrival_time",
        "price",
        "duration",
        "seat_availability"
    ]

    missing_fields = [
        field
        for field in required_fields
        if data.get(field) is None
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
            UPDATE flights
            SET
                airline = ?,
                origin = ?,
                destination = ?,
                departure_time = ?,
                arrival_time = ?,
                price = ?,
                duration = ?,
                image = ?,
                seat_availability = ?
            WHERE flight_id = ?
            """,
            (
                data["airline"],
                data["origin"],
                data["destination"],
                data["departure_time"],
                data["arrival_time"],
                data["price"],
                data["duration"],
                data.get("image"),
                data["seat_availability"],
                flight_id
            )
        )

        connection.commit()

        updated_rows = cursor.rowcount

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "A flight with this airline, route and departure time already exists"
        }), 409

    finally:
        connection.close()

    if updated_rows == 0:
        return jsonify({"error": "Flight not found"}), 404

    return jsonify({
        "flight_id": flight_id,
        "message": "Flight updated"
    }), 200


@app.route("/flights/<int:flight_id>", methods=["DELETE"])
def delete_flight(flight_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            "DELETE FROM flights WHERE flight_id = ?",
            (flight_id,)
        )

        connection.commit()

        deleted_rows = cursor.rowcount

    finally:
        connection.close()

    if deleted_rows == 0:
        return jsonify({"error": "Flight not found"}), 404

    return jsonify({
        "flight_id": flight_id,
        "message": "Flight deleted"
    }), 200

if __name__ == "__main__":
    initialise_database()
    app.run(host="0.0.0.0", port=6005)