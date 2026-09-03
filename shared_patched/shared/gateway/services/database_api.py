import os

import requests


SHARED_DATABASE_URL = os.getenv(
    "SHARED_DATABASE_URL",
    "http://shared-database:6000"
)

TIMEOUT = 5


def create_session(customer_id):

    return requests.post(
        f"{SHARED_DATABASE_URL}/sessions",
        json={
            "customer_id": customer_id
        },
        timeout=TIMEOUT
    )


def get_session(session_id):

    return requests.get(
        f"{SHARED_DATABASE_URL}/sessions/{session_id}",
        timeout=TIMEOUT
    )


def delete_session(session_id):

    return requests.delete(
        f"{SHARED_DATABASE_URL}/sessions/{session_id}",
        timeout=TIMEOUT
    )