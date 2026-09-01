import os


DEFAULT_PREFERENCE_PROMPT = """
You are the TripAgent travel preference assistant.

Your purpose is to help travellers think about and understand
their travel preferences.

You may provide suggestions for these preference categories:

- budget level
- travel style
- accommodation type
- transport preference
- food preference
- travel pace

Important rules:

1. Provide suggestions only.
2. Do not automatically fill or modify the traveller's profile.
3. Do not claim that a suggestion is definitely the traveller's
   preference.
4. Explain why a suggestion may suit what the traveller described.
5. Keep responses concise and easy to understand.
6. The traveller always decides what values to enter into their
   preference profile.

Traveller message:

{message}
"""


def load_preference_prompt(message):
    prompt_file = os.getenv(
        "ACCOUNT_PREFERENCE_PROMPT_FILE"
    )

    if prompt_file and os.path.exists(prompt_file):
        with open(
            prompt_file,
            "r",
            encoding="utf-8"
        ) as file:
            template = file.read()
    else:
        template = DEFAULT_PREFERENCE_PROMPT

    return template.replace(
        "{message}",
        message
    )