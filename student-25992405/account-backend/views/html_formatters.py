from html import escape


def format_ai_response(text):
    if not text:
        return ""

    escaped = escape(text)

    paragraphs = [
        paragraph.strip()
        for paragraph in escaped.split("\n")
        if paragraph.strip()
    ]

    return "<br>".join(paragraphs)