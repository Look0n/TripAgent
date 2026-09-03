import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request


app = Flask(__name__)

DATABASE_PATH = os.getenv(
    "SHARED_DATABASE_PATH",
    "/data/tripagent_access.db"
)

SESSION_HOURS = 24


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialise_database():

    directory = os.path.dirname(DATABASE_PATH)

    if directory:
        os.makedirs(directory, exist_ok=True)

    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS session (
                session_id TEXT PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "healthy",
        "service": "shared-database"
    }), 200


@app.route("/sessions", methods=["POST"])
def create_session():

    data = request.get_json(silent=True) or {}

    customer_id = data.get("customer_id")

    if customer_id is None:
        return jsonify({
            "error": "customer_id is required"
        }), 400

    session_id = secrets.token_urlsafe(32)

    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        hours=SESSION_HOURS
    )

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO session (
                session_id,
                customer_id,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                session_id,
                customer_id,
                now.isoformat(),
                expires_at.isoformat()
            )
        )

        connection.commit()

    finally:
        connection.close()

    return jsonify({
        "session_id": session_id,
        "customer_id": customer_id,
        "expires_at": expires_at.isoformat()
    }), 201


@app.route(
    "/sessions/<session_id>",
    methods=["GET"]
)
def get_session(session_id):

    connection = get_connection()

    try:
        record = connection.execute(
            """
            SELECT *
            FROM session
            WHERE session_id = ?
            """,
            (session_id,)
        ).fetchone()

    finally:
        connection.close()

    if record is None:
        return jsonify({
            "error": "Session not found"
        }), 404

    session_data = dict(record)

    expires_at = datetime.fromisoformat(
        session_data["expires_at"]
    )

    if datetime.now(timezone.utc) >= expires_at:

        delete_session_record(session_id)

        return jsonify({
            "error": "Session expired"
        }), 401

    return jsonify(
        session_data
    ), 200


def delete_session_record(session_id):

    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM session
            WHERE session_id = ?
            """,
            (session_id,)
        )

        connection.commit()

    finally:
        connection.close()


@app.route(
    "/sessions/<session_id>",
    methods=["DELETE"]
)
def delete_session(session_id):

    delete_session_record(session_id)

    return jsonify({
        "message": "Session removed"
    }), 200


@app.route(
    "/sessions/customer/<int:customer_id>",
    methods=["DELETE"]
)
def delete_customer_sessions(customer_id):

    connection = get_connection()

    try:
        connection.execute(
            """
            DELETE FROM session
            WHERE customer_id = ?
            """,
            (customer_id,)
        )

        connection.commit()

    finally:
        connection.close()

    return jsonify({
        "message": "Customer sessions removed"
    }), 200


if __name__ == "__main__":

    initialise_database()

    app.run(
        host="0.0.0.0",
        port=6000
    )