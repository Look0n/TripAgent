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
    "attractions": REPO_DIR / "student-25992374",
    "checklist": REPO_DIR / "student-25992424",
    "flight": REPO_DIR / "student-25992381",
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
    "attractions": [],
    "checklist": [],
    "flight": [],
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

def load_database_chunks(feature: str) -> list[dict[str, Any]]:
    feature = validate_feature(feature)
    if feature == "account":
        return load_account_database_chunks()
    if feature == "accommodation":
        return load_accommodation_database_chunks()

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

Answer the user's question using only the retrieved context below.

Rules:
- If any retrieved passage directly answers the question, use that evidence and answer concisely.
- Some retrieved passages may be unrelated. Ignore unrelated passages instead of treating them as a reason to reject the answer.
- Do not add facts that are not supported by the retrieved context.
- Only return exactly "Insufficient evidence." when none of the retrieved passages contains enough information to answer the question.
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
    
    if feature == "accommodation":
        relevant_results = [
            r for r in results
            if (
                r.get("source_id") == "rag-knowledge:accommodation"
                and r.get("distance") is not None
                and r.get("distance") <= 1.50
            )
        ]
        
        if not relevant_results:
            result = []
            answer = "Insufficient evidence."
    
    context = "\n\n".join(r.get("text", "") for r in results)
    answer = generate_with_ollama(query, context)
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
