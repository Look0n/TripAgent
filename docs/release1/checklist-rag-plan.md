# Checklist RAG implementation plan — 2026-10-02

Status: planning only. No RAG implementation or runtime verification performed in this update.

## Current verified code state

- Shared HTTP server already exposes GET /health and POST /rag/refresh, /rag/retrieve, /rag/answer on port 7002.
- FEATURE_DIRS.checklist is already student-14582668; do not repeat the old path correction.
- FEATURE_KNOWLEDGE.checklist is empty; checklist-corpus.jsonl is zero bytes.
- load_database_chunks has no Checklist branch and returns a contract_pending placeholder.
- generate_with_ollama catches errors and returns error text which answer_question can mark successful.
- Checklist gateway timeout is 30 seconds; shared nginx API read timeout is 120 seconds, while Ollama request timeout is 120 seconds.
- Account RAG client/routes provide a reference, but do not copy its mutable process-wide enable switch or permissive input coercion.
- User-supplied pytest evidence shows 39 passed (22 MCP routes, 12 CRUD, 5 AI); corrected live MCP verification and UI recovery results have not yet been supplied.

## Ordered implementation

1. Define Checklist source knowledge in rag_pipeline.py using verified feature behavior: task/packing, categories, priorities, completion, and AI suggestions requiring explicit save. Use stable chunk IDs and traceable sources. Do not invent travel/visa policy. Add real Checklist DB snapshot loader using the existing API contract; exclude placeholder/health/error messages from answer evidence. Preserve the previous usable corpus on refresh failure, and expose freshness/failure clearly.
2. Refresh only feature=checklist through existing HTTP server. Verify real chunk contents/counts, vector_store_status=ready, collection isolation and source metadata. The generated JSONL is output, not the primary manually edited knowledge source.
3. Add Checklist relevance/insufficient-context handling before LLM invocation. Exclude irrelevant results; do not rank authority ahead of relevance. Return an explicit insufficient-context outcome without calling Ollama when evidence is absent. Separate input errors, retrieval errors, Ollama unavailability and genuine grounded answers. Ensure citations refer to supplied context; confidence is a documented heuristic, not a calibrated probability. Extend shared HTTP error mapping as needed without breaking Account/Accommodation.
4. Add checklist-backend/services/rag_client.py and routes/rag_routes.py; register blueprint in app.py. Proposed routes: GET /api/checklist-items/rag/status and POST /refresh, /retrieve, /answer under that prefix. Fix feature=checklist and caller=checklist-backend server-side. Validate query as nonempty string and k as integer 1..20 (reject bool). RAG_ENABLED=false must not be overridden by a browser request. Validate response JSON/schema and handle timeouts.
5. Configure checklist backend RAG_SERVICE_URL=http://host.docker.internal:7002 and RAG_ENABLED. Local server uses OLLAMA_GENERATE_URL and OLLAMA_MODEL. Explicitly set PowerShell environment: starting Python does not automatically load the root .env. Use local Ollama for final Release 1 topology; check port 11434 ownership before switching away from the existing Docker Ollama. Proposed layered timeouts: Ollama 120s, backend RAG client 150s, gateway 180s, nginx 210s, with short health-check timeouts. These are initial budgets to validate, not measured guarantees.
6. Extend existing checklist.html/checklist.js/checklist.css with RAG status, question form, pending/error state, answer, citations, confidence category and insufficient-context display. Use existing authenticated gateway path. Keep corpus refresh as a developer action initially. Rebuild changed containers; reload/restart shared-frontend after upstream recreation/config changes. RAG answers do not automatically create Checklist records.
7. Add offline mocked tests and local real retrieval/answer verification. Cover field validation, feature isolation, OFF, server/LLM outages, no evidence, citations, DB snapshot freshness, CRUD/MCP regression. Use labelled relevant chunk IDs for at least three answerable benchmark queries plus unrelated/unanswerable queries. Record P@5/R@5, retrieval mode, corpus version/time, model and actual responses. Do not claim calibrated thresholds or semantic embeddings for the current hash-based embedding.
8. Save evidence under docs/evidence/release1/checklist/rag/<timestamp> and update CI to disable external AI/MCP/RAG calls while running mock tests. Complete shared agentic-loop RAG validation and report as a separate Release 1 integration deliverable, not as a replacement for live evidence.

## Execution topology

Browser :3000 -> gateway -> checklist backend :5004 -> local shared RAG HTTP :7002 -> Checklist collection + local Ollama :11434.

Use rag_http_server.py for the backend HTTP integration. rag_server.py is a separate MCP-facing entry point; starting both is unnecessary for this path. Retrieval can be verified before invoking Ollama. Grounded-answer completion requires a real local model response.

## Completion gate

Real Checklist corpus, healthy vector store, grounded answer through authenticated UI, inspectable citations/confidence, verified insufficient-context, explicit service failure, safe recovery, existing CRUD/MCP tests passing, saved local evidence, and separately tracked shared-loop validation.
