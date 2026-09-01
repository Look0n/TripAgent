import os

import requests


ACCOUNT_DATABASE_URL = os.getenv(
    "ACCOUNT_DATABASE_URL",
    "http://account-database:6001"
)


DEFAULT_TIMEOUT = 5


def create_customer(data):
    return requests.post(
        f"{ACCOUNT_DATABASE_URL}/customers",
        json=data,
        timeout=DEFAULT_TIMEOUT
    )


def get_customer(customer_id):
    return requests.get(
        f"{ACCOUNT_DATABASE_URL}/customers/{customer_id}",
        timeout=DEFAULT_TIMEOUT
    )


def get_customer_by_email(email):
    return requests.get(
        f"{ACCOUNT_DATABASE_URL}/customers/by-email",
        params={
            "email": email
        },
        timeout=DEFAULT_TIMEOUT
    )


def update_customer(customer_id, data):
    return requests.put(
        f"{ACCOUNT_DATABASE_URL}/customers/{customer_id}",
        json=data,
        timeout=DEFAULT_TIMEOUT
    )


def get_preferences(customer_id):
    return requests.get(
        f"{ACCOUNT_DATABASE_URL}/preferences/{customer_id}",
        timeout=DEFAULT_TIMEOUT
    )


def save_preferences(customer_id, data):
    return requests.put(
        f"{ACCOUNT_DATABASE_URL}/preferences/{customer_id}",
        json=data,
        timeout=DEFAULT_TIMEOUT
    )


def delete_preferences(customer_id):
    return requests.delete(
        f"{ACCOUNT_DATABASE_URL}/preferences/{customer_id}",
        timeout=DEFAULT_TIMEOUT
    )