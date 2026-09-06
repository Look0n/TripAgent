import json
import urllib.error
import urllib.request

from config.review_config import (
    OLLAMA_API_URL, OLLAMA_TIMEOUT_SECONDS, IMPLEMENTATION_MODEL, REVIEW_MODEL,
)


def run_ollama(prompt, context="", model=IMPLEMENTATION_MODEL):
    payload = {
        "model": model,
        "prompt": f"{prompt}\n\nContext:\n{context}" if context else prompt,
        "stream": False,
        "options": {"temperature": 0},
    }
    req = urllib.request.Request(
        OLLAMA_API_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Ollama HTTP {error.code} for {model}: {detail}") from error
    except (TimeoutError, urllib.error.URLError, OSError) as error:
        raise RuntimeError(f"Ollama connection/timeout failure for {model}: {error}") from error
    except (ValueError, UnicodeError) as error:
        raise RuntimeError(f"Invalid Ollama JSON response for {model}") from error
    if not isinstance(result, dict) or result.get("error"):
        raise RuntimeError(f"Ollama error response for {model}: {result}")
    output = result.get("response")
    if not isinstance(output, str) or not output.strip():
        raise RuntimeError(f"Empty Ollama response for {model}")
    return output.strip()


def run_implementation(prompt, context=""):
    return run_ollama(prompt, context, model=IMPLEMENTATION_MODEL)


def run_review(prompt, context=""):
    return run_ollama(prompt, context, model=REVIEW_MODEL)
