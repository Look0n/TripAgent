import json
import os
import time
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
import requests

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent.parent
CORPUS_DIR = BASE_DIR / "corpus"
AUDIT_PATH = BASE_DIR / "rag-audit.jsonl"
CHROMA_DIR = BASE_DIR / "chroma"

SUPPORTED_FEATURES = {
    "account",
    "accommodation",
    "attractions",
    "checklist",
    "flight",
}

FEATURE_DIRS = {
    "account": REPO_DIR / "student-25992405",
    "accommodation": REPO_DIR / "student-14649634",
    "attractions": REPO_DIR / "student-25693742",
    "checklist": REPO_DIR / "student-14582668",
    "flight": REPO_DIR / "student-25487036",
}

FEATURE_DATABASE_URLS = {
    "account": os.getenv("ACCOUNT_DATABASE_URL", "http://localhost:6001"),
    "accommodation": os.getenv("ACCOMMODATION_DATABASE_URL", "http://localhost:6002"),
    "attractions": os.getenv("ATTRACTIONS_DATABASE_URL", "http://localhost:6003"),
    "checklist": os.getenv("CHECKLIST_DATABASE_URL", "http://localhost:6004"),
    "flight": os.getenv("FLIGHT_DATABASE_URL", "http://localhost:6005"),
}

# Account is implemented first. Other feature loaders can be specialised by their owners.
FEATURE_KNOWLEDGE = {
    "account": [
        {
            "chunk_id": "account_knowledge_profile",
            "text": "TripAgent Account allows an authenticated customer to view and update their own customer profile.",
        },
        {
            "chunk_id": "account_knowledge_preferences",
            "text": "TripAgent Account supports travel preferences such as preferred budget, travel style, accommodation and activity interests.",
        },
        {
            "chunk_id": "account_knowledge_ai",
            "text": "AI preference suggestions are advisory. The customer reviews and saves the final travel preferences.",
        },
        {
            "chunk_id": "account_knowledge_security",
            "text": "Account profile and preference operations require an authenticated customer session and should operate on that customer's data.",
        },
    ],
    "accommodation": [
        {
            "chunk_id": "accommodation_knowledge_search",
            "text": (
                "TripAgent Accommodation allows users to browse, "
                "search, filter, and view accommodation records."
            ),
        },
        {
            "chunk_id": "accommodation_knowledge_filters",
            "text": (
                "Accommodation records can be searched using travel "
                "requirements including city, budget, and guest capacity."
            ),
        },
        {
            "chunk_id": "accommodation_knowledge_availability",
            "text": (
                "If accommodation availability information is missing "
                "or incomplete, the system returns an unknown availability "
                "status rather than assuming the accommodation is unavailable."
            ),
        },
        {
            "chunk_id": "accommodation_knowledge_ai",
            "text": (
                "The Accommodation Service provides AI-assisted "
                "recommendations using stored accommodation records."
            ),
        },
    ],
    "attractions": [
        {
            "chunk_id": "attractions_knowledge_search",
            "text": (
                "TripAgent Attractions allows users to browse, search, "
                "and filter attraction and tour records by city, "
                "category, and maximum price."
            ),
        },
        {
            "chunk_id": "attractions_knowledge_categories",
            "text": (
                "The categories of attractions available are "
                "Sightseeing, Culture, Adventure, Entertainment "
                "and Food & Drink."
            ),
        },
        {
            "chunk_id": "attractions_knowledge_reviews",
            "text": (
                "Each attraction can have customer reviews with a rating "
                "from 1 to 5. The average_rating field is recalculated "
                "automatically whenever a new review is submitted."
            ),
        },
        {
            "chunk_id": "attractions_knowledge_ai",
            "text": (
                "The Attractions Service provides AI-assisted "
                "recommendations using a Plan-Act-Observe-Adapt pattern: "
                "it extracts city, category, budget and preferences from "
                "a free-text request, filters real database candidates, "
                "and only then asks the LLM to explain the best matches."
            ),
        },
    ],
    "flight": [],
    "checklist": [
        {
            "chunk_id": "checklist_knowledge_item_types",
            "text": (
                "TripAgent Checklist supports two item types: task and packing. "
                "A task represents a preparation action, such as completing "
                "online check-in. A packing item represents something to bring, "
                "such as a passport or phone charger."
            ),
        },
        {
            "chunk_id": "checklist_knowledge_fields",
            "text": (
                "Each Checklist item has an item ID, title, item type, "
                "category, description, priority, and completion status. "
                "The title identifies the item. The description provides "
                "additional details. Category groups related items, "
                "such as Documents, Electronics, or Preparation."
            ),
        },
        {
            "chunk_id": "checklist_knowledge_priority",
            "text": (
                "Checklist priority must be High, Medium, or Low. "
                "Priority and completion are separate fields. "
                "An item can have High priority and still be completed. "
                "Users can filter Checklist items by priority."
            ),
        },
        {
            "chunk_id": "checklist_knowledge_completion",
            "text": (
                "Checklist completion status indicates whether an item "
                "has been completed. The database represents incomplete "
                "items with 0 and completed items with 1. "
                "The API accepts false for incomplete and true for completed. "
                "Updating completion does not delete the item."
            ),
        },
        {
            "chunk_id": "checklist_knowledge_operations",
            "text": (
                "TripAgent Checklist supports creating, viewing, updating, "
                "and deleting items. Users can filter the list by item type, "
                "category, priority, and completion status. "
                "An individual item can be retrieved using its item ID."
            ),
        },
        {
            "chunk_id": "checklist_knowledge_ai_suggestions",
            "text": (
                "Checklist AI recommendations are suggestions and are not "
                "saved automatically. Users review suggestions and explicitly "
                "choose Add to checklist to save an item. "
                "The backend returns at most five suggestions and filters "
                "suggestions whose titles already exist in the checklist."
            ),
        },
        {
            "chunk_id": "checklist_knowledge_snapshot",
            "text": (
                "Checklist database records in the RAG corpus are snapshots "
                "taken when the corpus is refreshed. Changes made after that "
                "refresh may not appear in RAG answers until the next refresh. "
                "Use the normal Checklist API or Checklist MCP tools to "
                "check the current stored items and counts."
            ),
        },
    ],
    "flight": [
        {
            "chunk_id": "flight_knowledge_search",
            "text": (
                "TripAgent Flight Search allows travellers to browse, "
                "search and filter flight records by origin airport and "
                "destination airport."
            ),
        },
        {
            "chunk_id": "flight_knowledge_crud",
            "text": (
                "The Flight Search Service supports full create, read, "
                "update and delete operations on flight records through "
                "its frontend and backend API."
            ),
        },
        {
            "chunk_id": "flight_knowledge_availability",
            "text": (
                "A flight with fewer than ten seats remaining is reported "
                "as limited availability. If seat availability is not "
                "recorded, the system returns an unknown availability "
                "status rather than assuming the flight is full."
            ),
        },
        {
            "chunk_id": "flight_knowledge_agentic",
            "text": (
                "Flight recommendations follow a Plan, Act, Observe, Adapt "
                "workflow. The Observe stage verifies retrieved flight data "
                "deterministically in code, computing the price and duration "
                "ranges and identifying the cheapest and quickest flights "
                "before the language model is called."
            ),
        },
        {
            "chunk_id": "flight_knowledge_grounding",
            "text": (
                "The Flight Search language model may only describe flights "
                "returned by the flight database query. It must not invent "
                "airlines, routes, prices or times, and the verified flight "
                "table is displayed alongside every generated recommendation."
            ),
        },
        {
            "chunk_id": "flight_knowledge_duplicates",
            "text": (
                "A flight is uniquely identified by its airline, origin, "
                "destination and departure time. Creating a duplicate "
                "returns an HTTP 409 conflict rather than a second record."
            ),
        },
    ],
}

EMBED_VECTOR_SIZE = 256
_collections: dict[str, Any] = {}
_last_corpus_chunks: dict[str, list[dict[str, Any]]] = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_feature(feature: str) -> str:
    value = str(feature or "").strip().lower()
    if value not in SUPPORTED_FEATURES:
        raise ValueError(f"Unsupported TripAgent feature: {value}")
    return value


def corpus_path(feature: str) -> Path:
    feature = validate_feature(feature)
    return CORPUS_DIR / f"{feature}-corpus.jsonl"


def chroma_path(feature: str) -> Path:
    path = CHROMA_DIR / validate_feature(feature)
    path.mkdir(parents=True, exist_ok=True)
    return path


def collection_name(feature: str) -> str:
    return f"tripagent_{validate_feature(feature)}_context"


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Lab-compatible deterministic 256-dimensional hash embeddings."""
    vectors: list[list[float]] = []
    for text in texts:
        values = [0.0] * EMBED_VECTOR_SIZE
        tokens = (text or "").lower().split()
        if not tokens:
            vectors.append(values)
            continue
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i, byte in enumerate(digest):
                values[i % EMBED_VECTOR_SIZE] += (byte / 255.0) - 0.5
        norm = sum(v * v for v in values) ** 0.5
        if norm > 0:
            values = [v / norm for v in values]
        vectors.append(values)
    return vectors


def get_collection(feature: str):
    feature = validate_feature(feature)
    if feature not in _collections:
        client = chromadb.PersistentClient(path=str(chroma_path(feature)))
        _collections[feature] = client.get_or_create_collection(name=collection_name(feature))
    return _collections[feature]


def reset_collection(feature: str) -> None:
    feature = validate_feature(feature)
    client = chromadb.PersistentClient(path=str(chroma_path(feature)))
    try:
        client.delete_collection(name=collection_name(feature))
    except Exception:
        pass
    _collections[feature] = client.get_or_create_collection(name=collection_name(feature))


def append_audit(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_output: dict[str, Any],
    validation_status: str,
    outcome: str,
    start_time: float,
) -> None:
    """Same audit shape used by the Lab 8 pipeline."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "request_id": str(uuid.uuid4()),
        "trace_id": str(uuid.uuid4()),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "timestamp": now_iso(),
        "duration_ms": int((time.time() - start_time) * 1000),
        "validation_status": validation_status,
        "outcome": outcome,
    }
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def chunk_text(text: str, max_words: int = 80) -> list[str]:
    words = text.split()
    if not words:
        return []
    return [
        " ".join(words[i:i + max_words]).strip()
        for i in range(0, len(words), max_words)
        if " ".join(words[i:i + max_words]).strip()
    ]


def _normalise_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("customers", "data", "results", "items"):
            if isinstance(payload.get(key), list):
                return [x for x in payload[key] if isinstance(x, dict)]
    return []


def load_account_database_chunks() -> list[dict[str, Any]]:
    """Tier 1: record Account database service availability without indexing customer data."""
    base_url = FEATURE_DATABASE_URLS["account"].rstrip("/")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        response.raise_for_status()
        return [{
            "chunk_id": "account_db_health",
            "source_id": "account-database:/health",
            "authority_tier": "tier_1",
            "text": "The TripAgent Account database service is available.",
            "metadata": {
                "source_type": "database_service",
                "metric": "health",
                "privacy_scope": "service-only",
            },
            "indexed_at": now_iso(),
        }]
    except Exception as exc:
        return [{
            "chunk_id": "account_db_unavailable",
            "source_id": "account-database:/health",
            "authority_tier": "tier_1",
            "text": "The TripAgent Account database service was unavailable when the corpus was refreshed.",
            "metadata": {
                "source_type": "database_service",
                "available": False,
                "privacy_scope": "service-only",
                "error_type": type(exc).__name__,
            },
            "indexed_at": now_iso(),
        }]
        
def load_accommodation_database_chunks() -> list[dict[str, Any]]:
    base_url = FEATURE_DATABASE_URLS["accommodation"].rstrip("/")

    try:
        response = requests.get(
            f"{base_url}/health",
            timeout=5,
        )
        response.raise_for_status()

        return [{
            "chunk_id": "accommodation_db_health",
            "source_id": "accommodation-database:/health",
            "authority_tier": "tier_1",
            "text": (
                "The TripAgent Accommodation database "
                "service is available."
            ),
            "metadata": {
                "source_type": "database_service",
                "metric": "health",
            },
            "indexed_at": now_iso(),
        }]

    except Exception as exc:
        return [{
            "chunk_id": "accommodation_db_unavailable",
            "source_id": "accommodation-database:/health",
            "authority_tier": "tier_1",
            "text": (
                "The TripAgent Accommodation database service "
                "was unavailable when the corpus was refreshed."
            ),
            "metadata": {
                "source_type": "database_service",
                "available": False,
                "error_type": type(exc).__name__,
            },
            "indexed_at": now_iso(),
        }]

def load_attractions_database_chunks() -> list[dict[str, Any]]:
    base_url = FEATURE_DATABASE_URLS["attractions"].rstrip("/")

    try:
        response = requests.get(
            f"{base_url}/health",
            timeout=5,
        )
        response.raise_for_status()

        return [{
            "chunk_id": "attractions_db_health",
            "source_id": "attractions-database:/health",
            "authority_tier": "tier_1",
            "text": (
                "The TripAgent Attractions database "
                "service is available."
            ),
            "metadata": {
                "source_type": "database_service",
                "metric": "health",
            },
            "indexed_at": now_iso(),
        }]

    except Exception as exc:
        return [{
            "chunk_id": "attractions_db_unavailable",
            "source_id": "attractions-database:/health",
            "authority_tier": "tier_1",
            "text": (
                "The TripAgent Attractions database service "
                "was unavailable when the corpus was refreshed."
            ),
            "metadata": {
                "source_type": "database_service",
                "available": False,
                "error_type": type(exc).__name__,
            },
            "indexed_at": now_iso(),
        }]


def load_flight_database_chunks() -> list[dict[str, Any]]:
    """Tier 1: record Flight database availability and non-sensitive route coverage."""
    base_url = FEATURE_DATABASE_URLS["flight"].rstrip("/")

    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        response.raise_for_status()
    except Exception as exc:
        return [{
            "chunk_id": "flight_db_unavailable",
            "source_id": "flight-database:/health",
            "authority_tier": "tier_1",
            "text": (
                "The TripAgent Flight database service was unavailable "
                "when the corpus was refreshed."
            ),
            "metadata": {
                "source_type": "database_service",
                "available": False,
                "error_type": type(exc).__name__,
            },
            "indexed_at": now_iso(),
        }]

    chunks = [{
        "chunk_id": "flight_db_health",
        "source_id": "flight-database:/health",
        "authority_tier": "tier_1",
        "text": "The TripAgent Flight database service is available.",
        "metadata": {
            "source_type": "database_service",
            "metric": "health",
        },
        "indexed_at": now_iso(),
    }]

    try:
        response = requests.get(f"{base_url}/flights", timeout=10)
        response.raise_for_status()
        flights = _normalise_records(response.json())
    except Exception:
        return chunks

    if not flights:
        return chunks

    airlines = sorted({
        str(f.get("airline")).strip()
        for f in flights
        if f.get("airline")
    })

    routes = sorted({
        f"{f.get('origin')}-{f.get('destination')}"
        for f in flights
        if f.get("origin") and f.get("destination")
    })

    prices = [
        float(f["price"])
        for f in flights
        if f.get("price") is not None
    ]

    chunks.append({
        "chunk_id": "flight_db_coverage",
        "source_id": "flight-database:/flights",
        "authority_tier": "tier_1",
        "text": (
            f"The TripAgent Flight database holds {len(flights)} flight "
            f"records covering {len(routes)} routes operated by "
            f"{len(airlines)} airlines. Airlines: {', '.join(airlines)}. "
            f"Routes: {', '.join(routes)}."
        ),
        "metadata": {
            "source_type": "database_service",
            "metric": "coverage",
            "record_count": len(flights),
            "route_count": len(routes),
        },
        "indexed_at": now_iso(),
    })

    if prices:
        chunks.append({
            "chunk_id": "flight_db_pricing",
            "source_id": "flight-database:/flights",
            "authority_tier": "tier_1",
            "text": (
                f"Flight fares in the TripAgent Flight database range from "
                f"${min(prices):.2f} to ${max(prices):.2f}."
            ),
            "metadata": {
                "source_type": "database_service",
                "metric": "pricing",
            },
            "indexed_at": now_iso(),
        })

    return chunks


def load_checklist_database_chunks() -> list[dict[str, Any]]:
    base_url = FEATURE_DATABASE_URLS["checklist"].rstrip("/")

    try:
        response = requests.get(
            f"{base_url}/checklist-items",
            timeout=10,
        )
        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            "Unable to load Checklist records from the database service."
        ) from exc

    try:
        items = response.json()

    except ValueError as exc:
        raise RuntimeError(
            "Checklist database returned invalid JSON."
        ) from exc

    if not isinstance(items, list):
        raise ValueError(
            "Checklist database must return a list of items."
        )

    chunks: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    indexed_at = now_iso()

    for item in items:
        if not isinstance(item, dict):
            raise ValueError(
                "Each Checklist record must be a JSON object."
            )

        item_id = item.get("item_id")
        title = item.get("title")
        item_type = item.get("item_type")
        priority = item.get("priority")
        is_completed = item.get("is_completed")
        category = item.get("category")
        description = item.get("description")

        if type(item_id) is not int or item_id < 1:
            raise ValueError(
                "Checklist records must have positive integer item IDs."
            )

        if item_id in seen_ids:
            raise ValueError(
                f"Duplicate Checklist item ID: {item_id}"
            )

        if not isinstance(title, str) or not title.strip():
            raise ValueError(
                f"Checklist item {item_id} has an invalid title."
            )

        if item_type not in ("task", "packing"):
            raise ValueError(
                f"Checklist item {item_id} has an invalid item type."
            )

        if priority not in ("High", "Medium", "Low"):
            raise ValueError(
                f"Checklist item {item_id} has an invalid priority."
            )

        if (
            type(is_completed) not in (int, bool)
            or is_completed not in (0, 1)
        ):
            raise ValueError(
                f"Checklist item {item_id} has an invalid completion status."
            )

        if category is not None and not isinstance(category, str):
            raise ValueError(
                f"Checklist item {item_id} has an invalid category."
            )

        if description is not None and not isinstance(description, str):
            raise ValueError(
                f"Checklist item {item_id} has an invalid description."
            )

        seen_ids.add(item_id)

        category_text = (category or "").strip() or "Not specified"
        description_text = (description or "").strip() or "Not specified"
        completion_text = (
            "completed" if is_completed == 1 else "incomplete"
        )

        record_text = (
            f"Checklist item ID: {item_id}. "
            f"Title: {title.strip()}. "
            f"Item type: {item_type}. "
            f"Category: {category_text}. "
            f"Priority: {priority}. "
            f"Completion status: {completion_text}. "
            f"Description: {description_text}. "
            f"This record is a database snapshot indexed at {indexed_at}."
        )

        for part_number, text in enumerate(
            chunk_text(record_text),
            start=1,
        ):
            chunks.append({
                "chunk_id": (
                    f"checklist_db_item_{item_id}_{part_number}"
                ),
                "source_id": (
                    f"checklist-database:/checklist-items/{item_id}"
                ),
                "authority_tier": "tier_1",
                "text": text,
                "metadata": {
                    "source_type": "database_record",
                    "feature": "checklist",
                    "item_id": item_id,
                    "item_type": item_type,
                    "priority": priority,
                    "is_completed": bool(is_completed),
                    "snapshot": True,
                },
                "indexed_at": indexed_at,
            })

    return chunks


def load_database_chunks(feature: str) -> list[dict[str, Any]]:
    feature = validate_feature(feature)
    if feature == "checklist":
        return load_checklist_database_chunks()
    if feature == "account":
        return load_account_database_chunks()
    if feature == "accommodation":
        return load_accommodation_database_chunks()
    if feature == "flight":
        return load_flight_database_chunks()
    if feature == "attractions":
        return load_attractions_database_chunks()

    # Placeholder for team features until their database contracts are known.
    return [{
        "chunk_id": f"{feature}_db_contract_pending",
        "source_id": f"{feature}-database",
        "authority_tier": "tier_1",
        "text": f"{feature.title()} database RAG source mapping has not yet been configured.",
        "metadata": {"source_type": "database_service", "configured": False},
        "indexed_at": now_iso(),
    }]


def load_knowledge_chunks(feature: str) -> list[dict[str, Any]]:
    feature = validate_feature(feature)
    return [{
        **item,
        "source_id": f"rag-knowledge:{feature}",
        "authority_tier": "tier_2",
        "metadata": {"source_type": "feature_knowledge", "feature": feature},
        "indexed_at": now_iso(),
    } for item in FEATURE_KNOWLEDGE.get(feature, [])]


def load_report_chunks(feature: str) -> list[dict[str, Any]]:
    """Tier 2: feature-owned reports when present."""
    feature = validate_feature(feature)
    feature_dir = FEATURE_DIRS.get(feature)
    if not feature_dir or not feature_dir.exists():
        return []

    chunks: list[dict[str, Any]] = []
    report_names = {
        "report.json", "run-report.md", "integration-report.md",
        "tool-review.md", "boundary-analysis.md"
    }
    for path in feature_dir.rglob("*"):
        if not path.is_file() or path.name not in report_names:
            continue
        try:
            if path.suffix == ".json":
                text = json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2)
            else:
                text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, piece in enumerate(chunk_text(text), 1):
            chunks.append({
                "chunk_id": f"{feature}_report_{path.stem}_{i}",
                "source_id": str(path.relative_to(REPO_DIR)).replace("\\", "/"),
                "authority_tier": "tier_2",
                "text": piece,
                "metadata": {"source_type": "report", "file": path.name},
                "indexed_at": now_iso(),
            })
    return chunks


def load_repository_chunks(feature: str) -> list[dict[str, Any]]:
    """Tier 3: index only the selected feature's repository subtree."""
    feature = validate_feature(feature)
    feature_dir = FEATURE_DIRS.get(feature)
    if not feature_dir or not feature_dir.exists():
        return []

    ignored = {".git", ".venv", "__pycache__", "node_modules", "chroma"}
    files: list[str] = []
    for root, dirs, filenames in os.walk(feature_dir, topdown=True, followlinks=False):
        dirs[:] = [d for d in dirs if d not in ignored and not (Path(root) / d).is_symlink()]
        for filename in filenames:
            path = Path(root) / filename
            try:
                if not path.is_symlink():
                    files.append(str(path.relative_to(REPO_DIR)).replace("\\", "/"))
            except (OSError, ValueError):
                continue

    if not files:
        return []
    return [{
        "chunk_id": f"{feature}_repo_index",
        "source_id": f"repository:{feature}",
        "authority_tier": "tier_3",
        "text": f"{feature.title()} repository files include: " + ", ".join(sorted(files[:400])),
        "metadata": {"source_type": "repository", "feature": feature, "file_count": len(files)},
        "indexed_at": now_iso(),
    }]


def build_corpus(feature: str) -> list[dict[str, Any]]:
    feature = validate_feature(feature)
    chunks: list[dict[str, Any]] = []
    chunks.extend(load_database_chunks(feature))
    chunks.extend(load_knowledge_chunks(feature))
    chunks.extend(load_report_chunks(feature))
    chunks.extend(load_repository_chunks(feature))
    return chunks


def write_corpus(feature: str, chunks: list[dict[str, Any]]) -> None:
    path = corpus_path(feature)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")


def read_corpus(feature: str) -> list[dict[str, Any]]:
    path = corpus_path(feature)
    if not path.exists():
        return []
    chunks = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                if line.strip():
                    chunks.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return chunks


def lexical_fallback_retrieve(query: str, feature: str, k: int) -> list[dict[str, Any]]:
    feature = validate_feature(feature)
    corpus = _last_corpus_chunks.get(feature) or read_corpus(feature)
    query_tokens = set((query or "").lower().split())
    tier_weight = {"tier_1": 3, "tier_2": 2, "tier_3": 1}
    scored = []
    for chunk in corpus:
        text = chunk.get("text", "")
        overlap = len(query_tokens.intersection(set(text.lower().split())))
        scored.append({
            "rank": 0,
            "chunk_id": chunk.get("chunk_id"),
            "source_id": chunk.get("source_id"),
            "authority_tier": chunk.get("authority_tier"),
            "distance": None,
            "text": text,
            "_score": overlap,
        })
    scored.sort(key=lambda r: (tier_weight.get(r.get("authority_tier"), 0), r["_score"]), reverse=True)
    top = scored[:max(int(k), 1)]
    for i, row in enumerate(top, 1):
        row["rank"] = i
        row.pop("_score", None)
    return top


def refresh_corpus(feature: str, caller: str = "student") -> dict[str, Any]:
    feature = validate_feature(feature)
    start = time.time()
    try:
        chunks = build_corpus(feature)
        _last_corpus_chunks[feature] = chunks
        write_corpus(feature, chunks)
        vector_store_status = "ready"
        vector_store_error = None
        try:
            reset_collection(feature)
            collection = get_collection(feature)
            if chunks:
                collection.add(
                    ids=[c["chunk_id"] for c in chunks],
                    documents=[c["text"] for c in chunks],
                    metadatas=[{
                        "source_id": c["source_id"],
                        "authority_tier": c["authority_tier"],
                        "indexed_at": c["indexed_at"],
                        "feature": feature,
                    } for c in chunks],
                    embeddings=embed_texts([c["text"] for c in chunks]),
                )
        except Exception as exc:
            vector_store_status = "degraded"
            vector_store_error = str(exc)

        output = {
            "status": "success",
            "feature": feature,
            "caller": caller,
            "chunk_count": len(chunks),
            "collection": collection_name(feature),
            "corpus_path": str(corpus_path(feature)),
            "vector_store_status": vector_store_status,
        }
        if vector_store_error:
            output["vector_store_error"] = vector_store_error
        append_audit("refresh_corpus",
                     {"feature": feature, "caller": caller},
                     output, "pass", "corpus_refreshed", start)
        return output
    except Exception as exc:
        output = {"status": "error", "feature": feature, "error": str(exc)}
        append_audit("refresh_corpus",
                     {"feature": feature, "caller": caller},
                     output, "fail", "error", start)
        return output


def retrieve_context(query: str, feature: str, k: int = 5, caller: str = "student") -> dict[str, Any]:
    feature = validate_feature(feature)
    start = time.time()
    query = str(query or "").strip()
    if not query:
        return {"status": "error", "feature": feature, "error": "query_required"}

    try:
        retrieval_mode = "vector"
        ranked = []
        try:
            collection = get_collection(feature)
            if collection.count() == 0:
                refreshed = refresh_corpus(feature, caller="auto_refresh")
                if refreshed.get("status") != "success":
                    raise RuntimeError("empty_collection")
            count = collection.count()
            results = collection.query(
                query_embeddings=embed_texts([query]),
                n_results=min(max(int(k), 1), count),
            )
            ids = (results.get("ids") or [[]])[0]
            docs = (results.get("documents") or [[]])[0]
            metas = (results.get("metadatas") or [[]])[0]
            distances = (results.get("distances") or [[]])[0]
            for i, chunk_id in enumerate(ids):
                meta = metas[i] if i < len(metas) and isinstance(metas[i], dict) else {}
                ranked.append({
                    "rank": i + 1,
                    "chunk_id": chunk_id,
                    "source_id": meta.get("source_id"),
                    "authority_tier": meta.get("authority_tier"),
                    "distance": distances[i] if i < len(distances) else None,
                    "text": docs[i] if i < len(docs) else "",
                })
            # Chroma already returns results in semantic relevance order.
            # Preserve that order so the best semantic match remains the top chunk.
            # Authority tier is retained as metadata and is used by confidence scoring.
        except Exception:
            retrieval_mode = "lexical_fallback"
            if not _last_corpus_chunks.get(feature) and not corpus_path(feature).exists():
                refreshed = refresh_corpus(feature, caller="auto_refresh")
                if refreshed.get("status") != "success":
                    return {"status": "error", "feature": feature, "error": "corpus_unavailable"}
            ranked = lexical_fallback_retrieve(query, feature, k)

        output = {
            "status": "success", "feature": feature, "query": query,
            "caller": caller, "k": k, "retrieval_mode": retrieval_mode,
            "results": ranked,
        }
        append_audit(
            "retrieve_context",
            {"feature": feature, "query": query, "k": k, "caller": caller},
            {"result_count": len(ranked), "chunk_ids": [r["chunk_id"] for r in ranked]},
            "pass", "context_retrieved", start)
        return output
    except Exception as exc:
        output = {"status": "error", "feature": feature, "query": query, "error": str(exc)}
        append_audit(
            "retrieve_context",
            {"feature": feature, "query": query, "k": k, "caller": caller},
            output, "fail", "error", start)
        return output


def confidence_from_results(results: list[dict[str, Any]]) -> str:
    if not results:
        return "Unknown"
    tier_1 = sum(1 for r in results if r.get("authority_tier") == "tier_1")
    tier_2 = sum(1 for r in results if r.get("authority_tier") == "tier_2")
    if tier_1 >= 2 and len(results) >= 3:
        return "High"
    if tier_1 >= 1 or tier_2 >= 2:
        return "Medium"
    return "Low"


def generate_with_ollama(query: str, context: str) -> str:
    model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
    ollama_generate_url = os.getenv("OLLAMA_GENERATE_URL", "http://localhost:11434/api/generate")
    prompt = f"""You are the TripAgent retrieval-grounded assistant.

Every passage below was selected because it is relevant to the question.
Answer the question using only the information stated in these passages.

Rules:
- Answer in two or three sentences using only facts that appear in the passages.
- Do not add any fact that is not stated in the passages.
- Do not use your own general knowledge, even if you believe the answer.
- Do not claim the evidence is insufficient. Relevance has already been checked.
- Return only the answer text. Do not add headings such as "Answer" or "Evidence".

QUESTION:
{query}

RETRIEVED CONTEXT:
{context}

ANSWER:
"""
    try:
        resp = requests.post(
            ollama_generate_url,
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "Insufficient evidence.")
    except Exception as exc:
        return f"Ollama unavailable: {exc}"


STOPWORDS = {
    "a", "about", "an", "and", "any", "are", "as", "at", "be", "been", "by",
    "can", "did", "do", "doe", "for", "from", "ha", "had", "how", "i", "if",
    "in", "into", "is", "it", "many", "me", "much", "my", "of", "on", "or",
    "our", "that", "the", "their", "there", "thi", "to", "wa", "what", "when",
    "where", "which", "who", "why", "will", "with", "you", "your",
}

MODEL_REFUSAL_PREFIXES = (
    "insufficient evidence",
    "insufficient context",
    "i do not have enough",
    "i don't have enough",
)


def content_words(text: str) -> set[str]:
    """Lower-case, de-pluralised, stopword-free tokens used for relevance scoring."""
    tokens = {
        word.strip(".,?!:;\"'()[]").rstrip("s")
        for word in str(text or "").lower().split()
    }
    return {word for word in tokens if len(word) > 2 and word not in STOPWORDS}


def is_model_refusal(answer: str) -> bool:
    """True when the model declined to answer despite being given relevant context."""
    cleaned = str(answer or "").strip().lower().lstrip('"').rstrip('."')
    return any(cleaned.startswith(prefix) for prefix in MODEL_REFUSAL_PREFIXES)


def filter_relevant_results(
    results: list[dict[str, Any]],
    query: str,
    min_overlap: int = 2,
) -> list[dict[str, Any]]:
    """Keep only passages that share meaningful terms with the query.

    Authority tier is deliberately not a free pass. A tier_1 service fact is
    authoritative about the flight service, not about every question asked of
    it, so an off-topic query must be able to retain nothing at all.
    """
    query_words = content_words(query)
    if not query_words:
        return []

    relevant: list[dict[str, Any]] = []

    for row in results:
        overlap = query_words & content_words(row.get("text", ""))
        if len(overlap) >= min_overlap:
            relevant.append(row)

    return relevant


def insufficient_context_response(
    feature: str,
    query: str,
    k: int,
    retrieval: dict[str, Any],
) -> dict[str, Any]:
    """Structured response used when no retrieved passage supports an answer."""
    return {
        "status": "success",
        "feature": feature,
        "query": query,
        "answer": (
            "Insufficient context. The shared RAG corpus for this feature "
            "does not contain information that answers this question, so no "
            "grounded answer was generated."
        ),
        "insufficient_context": True,
        "citations": [],
        "confidence_category": "Unknown",
        "retrieval_summary": {
            "k": k,
            "retrieved_count": 0,
            "top_chunk": None,
            "retrieval_mode": retrieval.get("retrieval_mode"),
        },
    }


def answer_question(query: str, feature: str, k: int = 5, caller: str = "student") -> dict[str, Any]:
    feature = validate_feature(feature)
    start = time.time()
    retrieval = retrieve_context(query=query, feature=feature, k=k, caller=caller)
    if retrieval.get("status") != "success":
        output = {"status": "error", "feature": feature, "query": query,
                  "error": retrieval.get("error", "retrieval_failed")}
        append_audit("answer_question",
                     {"feature": feature, "query": query, "k": k, "caller": caller},
                     output, "fail", "retrieval_failed", start)
        return output

    results = retrieval.get("results", [])

    if feature == "flight":
        results = filter_relevant_results(results, query)

    if feature == "accommodation":
        query_words = {
            word.strip(".,?!").rstrip("s")
            for word in query.lower().split()
        }

        relevant_results = []

        for r in results:
            if r.get("source_id") != "rag-knowledge:accommodation":
                continue

            text_words = {
                word.rstrip("s")
                for word in r.get("text", "").lower().split()
            }

            if len(query_words & text_words) >= 2:
                relevant_results.append(r)

        results = relevant_results

    if feature == "attractions":
        # The feature name appears in almost every attractions chunk, so it
        # cannot count as evidence on its own; any other shared term can.
        query_words = content_words(query) - {"attraction", "tripagent"}
        results = [
            r for r in results
            if query_words & content_words(r.get("text", ""))
        ]

    if not results:
        output = insufficient_context_response(feature, query, k, retrieval)
        append_audit(
            "answer_question",
            {"feature": feature, "query": query, "k": k, "caller": caller},
            {"confidence_category": "Unknown", "citation_count": 0},
            "pass", "insufficient_context", start)
        return output

    context = "\n\n".join(r.get("text", "") for r in results)
    answer = generate_with_ollama(query, context)

    if is_model_refusal(answer):
        output = insufficient_context_response(feature, query, k, retrieval)
        append_audit(
            "answer_question",
            {"feature": feature, "query": query, "k": k, "caller": caller},
            {"confidence_category": "Unknown", "citation_count": 0},
            "pass", "insufficient_context_model_declined", start)
        return output

    citations = [{
        "chunk_id": r.get("chunk_id"),
        "source_id": r.get("source_id"),
        "authority_tier": r.get("authority_tier"),
    } for r in results]
    confidence = confidence_from_results(results)
    output = {
        "status": "success",
        "feature": feature,
        "query": query,
        "answer": answer,
        "insufficient_context": False,
        "citations": citations,
        "confidence_category": confidence,
        "retrieval_summary": {
            "k": k,
            "retrieved_count": len(results),
            "top_chunk": results[0].get("chunk_id") if results else None,
            "retrieval_mode": retrieval.get("retrieval_mode"),
        },
    }
    append_audit(
        "answer_question",
        {"feature": feature, "query": query, "k": k, "caller": caller},
        {"confidence_category": confidence, "citation_count": len(citations)},
        "pass", "answer_generated", start)
    return output


if __name__ == "__main__":
    print(json.dumps(refresh_corpus("account"), indent=2))
    print(json.dumps(retrieve_context("What are travel preferences?", "account", 5), indent=2))
    print(json.dumps(answer_question("What are travel preferences?", "account", 5), indent=2))
