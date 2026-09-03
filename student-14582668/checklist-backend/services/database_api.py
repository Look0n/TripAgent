import os

import requests


CHECKLIST_DATABASE_URL = os.getenv(
    "CHECKLIST_DATABASE_URL",
    "http://127.0.0.1:6005"
).rstrip("/")

DEFAULT_TIMEOUT = 5


def get_checklist_items(params=None):
    return requests.get(
        f"{CHECKLIST_DATABASE_URL}/checklist-items",
        params=params or {},
        timeout=DEFAULT_TIMEOUT
    )


def get_checklist_item(item_id):
    return requests.get(
        f"{CHECKLIST_DATABASE_URL}/checklist-items/{item_id}",
        timeout=DEFAULT_TIMEOUT
    )


def create_checklist_item(data):
    return requests.post(
        f"{CHECKLIST_DATABASE_URL}/checklist-items",
        json=data,
        timeout=DEFAULT_TIMEOUT
    )


def update_checklist_item(item_id, data):
    return requests.put(
        f"{CHECKLIST_DATABASE_URL}/checklist-items/{item_id}",
        json=data,
        timeout=DEFAULT_TIMEOUT
    )


def delete_checklist_item(item_id):
    return requests.delete(
        f"{CHECKLIST_DATABASE_URL}/checklist-items/{item_id}",
        timeout=DEFAULT_TIMEOUT
    )
