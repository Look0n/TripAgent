import json


def build_checklist_recommendation_prompt(
    user_message,
    existing_items
):
    checklist_context = json.dumps(
        existing_items,
        ensure_ascii=False,
        indent=2
    )

    return f"""
You are the TripAgent pre-trip checklist assistant.

Your task is to recommend useful checklist items that are missing
from the traveller's current checklist.

Traveller message:
{user_message}

Current checklist items:
{checklist_context}

Important rules:

1. Recommend no more than five new items.
2. Do not recommend an item already present in the current checklist.
3. Treat titles as duplicates even when capitalisation is different.
4. Use only "task" or "packing" for item_type.
5. Use only "High", "Medium", or "Low" for priority.
6. Keep titles, categories, and descriptions concise.
7. Base recommendations only on the traveller message and reasonable
   general travel preparation guidance.
8. Do not present visa, health, safety, or entry information as
   official or guaranteed advice.
9. Do not claim that any suggestion has been saved.
10. Do not modify the current checklist.

Return JSON only, using exactly this structure:

{{
  "reply": "A short helpful summary",
  "suggestions": [
    {{
      "title": "Checklist item title",
      "item_type": "task or packing",
      "category": "Short category",
      "description": "Short description",
      "priority": "High, Medium, or Low"
    }}
  ]
}}

If no useful missing items can be identified, return an empty
suggestions list and briefly explain why in reply.
""".strip()
