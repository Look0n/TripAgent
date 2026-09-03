def build_extraction_prompt(user_message):

    return f"""
You are extracting attraction and tour search
requirements from a traveller message.

Return JSON only.

Use exactly these fields:

{{
    "city": string or null,
    "category": string or null,
    "budget": number or null,
    "preferences": []
}}

The category field should only be used when the
traveller clearly asks for a formal category such
as Sightseeing, Culture, Adventure, Entertainment,
or Food & Drink.

The preferences field should contain traveller
preferences such as:

- family friendly
- outdoors
- museum
- food
- relaxing
- adrenaline
- free
- iconic landmark
- local experience

Important rules:

1. Do not invent information.

2. If the traveller asks for a vibe or interest such
as "food tour" or "something adventurous", put that
information in preferences rather than category.

Example:

"Find a cheap outdoor activity in Sydney"

Return:

{{
    "city": "Sydney",
    "category": null,
    "budget": null,
    "preferences": [
        "outdoors",
        "cheap"
    ]
}}

Traveller message:

{user_message}
"""


def build_chat_recommendation_prompt(
    user_message,
    requirements,
    attractions
):

    attraction_text = ""

    for attraction in attractions:

        attraction_text += f"""
Attraction:
Name: {attraction.get("name")}
Category: {attraction.get("category")}
City: {attraction.get("city")}
Price: ${attraction.get("price")}
Rating: {attraction.get("average_rating")}
Description: {attraction.get("description")}

---
"""

    return f"""
You are an attractions and tour recommendation assistant.

Traveller message:

{user_message}


Extracted requirements:

{requirements}


Available attraction candidates:

{attraction_text}


Recommend attractions only from the provided candidates.

Important rules:

1. Recommend at most 3 attractions.

2. If only 1 or 2 suitable attractions exist, recommend
only that many.

3. Do not invent prices, locations, or features.

4. Prioritise matches based on city, budget, category,
traveller preferences, description, and rating.

5. Briefly explain why each recommendation matches the
traveller's request.

6. If none of the candidates reasonably match, say so
rather than inventing a match.

Return recommendations in this format:

1. Attraction Name
Reason: ...

2. Attraction Name
Reason: ...

Keep the response concise and helpful.
"""
