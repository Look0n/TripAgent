import json


def build_extraction_prompt(user_message):
    return f"""
You are an accommodation request parser.

Extract the traveller's requirements from the message below.

Traveller message:
{user_message}

Return ONLY valid JSON using this structure:

{{
    "city": null,
    "budget": null,
    "guests": null,
    "type": null,
    "preferences": []
}}

Rules:
- budget means maximum price per night.
- guests must be an integer if mentioned.
- type should be Hotel, Resort, Guesthouse, Apartment, or null.
- preferences should contain natural-language preferences such as
  quiet, luxury, near CBD, airport access, waterfront, etc.
- If something is not mentioned, use null.
"""


def build_chat_recommendation_prompt(
    user_message,
    requirements,
    accommodations
):
    candidate_text = ""

    for accommodation in accommodations:
        candidate_text += f"""
Accommodation ID: {accommodation['accommodation_id']}
Name: {accommodation['accommodation_name']}
Type: {accommodation['type']}
City: {accommodation['city']}
Address: {accommodation['address']}
Price per night: ${accommodation['price_per_night']}
Guest capacity: {accommodation['guest_capacity']}
Rating: {accommodation['rating']}
Description: {accommodation['description']}
-----------------------------
"""

    preferences = requirements.get(
        "preferences",
        []
    )

    return f"""
You are an accommodation assistant.

Traveller request:
"{user_message}"

Extracted requirements:
{json.dumps(requirements)}

Matching accommodations:

{candidate_text}

Recommend the best 1 to 3 accommodations.

Rules:
- ONLY use accommodations listed above.
- Do NOT invent hotels, prices, ratings, facilities,
  distances or locations.
- Consider these preferences:
  {preferences}
- Use the description, price, rating, type,
  city and guest capacity.
- Keep the response concise and useful.
"""