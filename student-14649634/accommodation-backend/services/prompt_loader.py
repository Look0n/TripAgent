import json


def build_extraction_prompt(user_message):

    return f"""
You are extracting accommodation search
requirements from a traveller message.

Return JSON only.

Use exactly these fields:

{{
    "city": string or null,
    "budget": number or null,
    "guests": number or null,
    "type": string or null,
    "preferences": []
}}

Guests convert the number of travellers into an integer.

Examples:
"for three people" -> 3
"for four guests" -> 4
"two adults and one child" -> 3
"family of five" -> 5

If the number of guests is not clear,
use null.

The preferences field should contain
traveller preferences such as:

- family friendly
- close to CBD
- resort style
- waterfront
- luxury
- quiet
- business friendly
- romantic
- city centre
- airport access
- spacious rooms
- relaxing atmosphere

Important rules:

1. Do not invent information.

2. If the traveller asks for a style
or vibe such as "resort", "luxury",
"family friendly", or "close to CBD",
put that information in preferences.

3. Accommodation type should only be
used when the traveller clearly asks
for a formal accommodation category.

For example:

"Recommend a family accommodation
in Sydney close to the CBD"

Return:

{{
    "city": "Sydney",
    "budget": null,
    "guests": null,
    "type": null,
    "preferences": [
        "family friendly",
        "close to CBD"
    ]
}}

Example:

"Recommend a resort style place
in Cairns"

Return:

{{
    "city": "Cairns",
    "budget": null,
    "guests": null,
    "type": null,
    "preferences": [
        "resort style"
    ]
}}

Example:

"Find a hotel in Melbourne under $300"

Return:

{{
    "city": "Melbourne",
    "budget": 300,
    "guests": null,
    "type": "Hotel",
    "preferences": []
}}

Traveller message:

{user_message}
"""

def build_chat_recommendation_prompt(
    user_message,
    requirements,
    accommodations
):

    accommodation_text = ""

    for accommodation in accommodations:

        accommodation_text += f"""
Accommodation:
Name: {accommodation.get("accommodation_name")}
Type: {accommodation.get("type")}
City: {accommodation.get("city")}
Address: {accommodation.get("address")}
Price per night: ${accommodation.get("price_per_night")}
Guest capacity: {accommodation.get("guest_capacity")}
Rating: {accommodation.get("rating")}
Description: {accommodation.get("description")}

---
"""


    return f"""
You are an accommodation recommendation assistant.

Traveller message:

{user_message}


Extracted requirements:

{requirements}


Available accommodation candidates:

{accommodation_text}


Recommend accommodations only from the provided candidates.

Important rules:

1. Recommend at most 3 accommodations.

2. If only 1 suitable accommodation exists, recommend only 1. 
If only 2 suitable accommodations exist, recommend only 2.

2. Do not invent facilities,
locations, prices, or features.

3. Use the accommodation description
when evaluating traveller preferences.

4. Accommodation type does not need
to exactly match a requested style.

For example:

- A property with type "Hotel"
can still match a "resort-style"
request if its description clearly
mentions a tropical, relaxing,
holiday, pool, or resort-like atmosphere.

- A hotel can match a family request
if its description, guest capacity,
or features suggest that it is
suitable for families.

- A property can match "close to CBD"
if the description or address clearly
supports that.

5. Prioritise matches based on:

- city
- budget
- guest capacity
- traveller preferences
- description
- rating

6. Briefly explain why each
recommendation matches the user's
request.

7. If none of the candidates reasonably
match the traveller's preferences,
say so rather than inventing a match.

Return recommendations in this format:

1. Accommodation Name
Reason: ...

2. Accommodation Name
Reason: ...

Only include numbering that corresponds
to actual recommendations.

Keep the response concise and helpful.
"""