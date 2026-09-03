import os


SERVICE_ROUTES = {

    "account": os.getenv(
        "ACCOUNT_BACKEND_URL",
        "http://account-backend:5001"
    ),

    "accommodation": os.getenv(
        "ACCOMMODATION_BACKEND_URL",
        "http://accommodation-backend:5002"
    ),

    "attractions": os.getenv(
        "ATTRACTIONS_BACKEND_URL",
        "http://attractions-backend:5003"
    ),

    "itinerary": os.getenv(
        "ITINERARY_BACKEND_URL",
        "http://itinerary-backend:5004"
    ),

    "flight": os.getenv(
        "FLIGHT_BACKEND_URL",
        "http://flight-backend:5005"
    )
}


def get_service_url(service_name):

    return SERVICE_ROUTES.get(
        service_name
    )