# Release 2 Evidence — Attractions & Tour Experiences

Student: Abdulloh Juraboev (25693742)
Feature: attractions
Captured: 23 October 2026

## Environment

| Component | Where it runs | Port |
|---|---|---|
| attractions-frontend / attractions-backend / attractions-database | Docker Compose | 3003 / 5003 / 6003 |
| AI-Mode LLM (Ollama, `qwen2.5:0.5b`) | host, non-containerised | 11434 |
| Shared MCP Server | host, non-containerised | 7001 |
| Shared RAG Server | host, non-containerised | 7002 |
| Shared Multi-Agent Server | host, non-containerised | 7003 |
| Planner model | Ollama | qwen2.5:0.5b |
| Worker and Reviewer model | Ollama | llama3.1:8b |

The containerised attractions backend reaches Ollama and the three shared
services through `host.docker.internal` (`extra_hosts: host-gateway` in
`docker-compose.yml`).

## Evidence index

| File | Shows | Criterion |
|---|---|---|
| `multi-agent-terminal.log` | Planner → Worker → Reviewer → Human Review run from the terminal through the attractions backend/API (`student-25693742/scripts/multi_agent_demo.py`), workflow history, and human-review validation (400 / 409 responses) | 2 |
| `multi-agent-audit.log` | Coordination/audit trail from the Multi-Agent Server for all attractions workflows: created → planner → worker → awaiting review → human decision | 2 |
| `multi-agent-ui-1-panel.jpg` | Multi-Agent panel on the attractions page, reached through the shared frontend | 2 |
| `multi-agent-ui-2-planner.jpg` | Planner plan rendered in the frontend | 2 |
| `multi-agent-ui-3-worker-reviewer-evidence.jpg` | Worker recommendations, Reviewer verdict and the database records supplied as evidence | 2 |
| `multi-agent-ui-4-human-review.jpg` | Human Review controls with a correction entered | 2 |
| `multi-agent-ui-5-decision-history.jpg` | Recorded Reject decision with correction and the workflow history (Accept, Partially Accept, Reject) | 2 |
| `pre-commit-security-scan.log` | Ruff security rules, detect-secrets and pip-audit on the attractions service | 3 |
| `endpoint-tests.log` | Post-commit endpoint tests (31 passed with CI flags) and the full suite against the live database (35 passed) | 4 |
| `ci-steps-local-run.log` | The `student-25693742-ci.yml` verification steps run locally with the CI environment | 4 |
| `local-deployment-multi-terminal.log` | Multi-terminal local deployment: Docker Compose services, the three host servers, and AI-Mode, MCP, RAG and Multi-Agent reached through the attractions backend | 1 |

## Post-commit endpoint tests

`student-25693742-ci.yml` runs `tests/test_endpoint_functions.py` on every push
and pull request that touches the attractions service:

| Endpoint function | Tests |
|---|---|
| `GET /api/attractions` (list / search) | returns records, forwards search/city/category/max_price filters, rejects a non-numeric `max_price` (400), returns 503 when the database is down |
| `POST /api/attractions` (create) | returns 201 with the created record, requires name/category/city/price (400), validates price (400), returns 503 when the database is down |

The database is stubbed in these tests, so they run before any container is
started. The workflow then starts the real containers and repeats both endpoint
functions live (list Paris attractions, create → read → invalid create → delete).
Results are uploaded as the `student-25693742-endpoint-tests` artifact.

## Multi-Agent design notes

The attractions backend collects candidate records from the attractions
database (filtered by city, category and maximum price) and sends them to the
Multi-Agent Server as `context.evidence` with `constraints.evidence_only = true`
and `bookings_allowed = false`. The attractions Worker prompt forbids inventing
attractions, prices or ratings, and the Reviewer checks every recommended
`attraction_id` against that evidence. The human decision is recorded on the
Multi-Agent Server; nothing is written to the attractions database.

Multi-Agent Mode is off when the backend starts and is switched on from the
frontend. `MULTI_AGENT_LOCKED=true` forces it off and refuses to enable it.

## Cloud baseline switches

| Service | Startup switch (local default) | Disabled behaviour |
|---|---|---|
| AI-Mode | `AI_MODE_ENABLED` (on) | `POST /api/attractions/recommend` → 403 |
| MCP | `MCP_ENABLED` (on) | MCP tool routes → 403 |
| RAG | `RAG_ENABLED` (on) | `/api/attractions/rag*` → 403 |
| Multi-Agent | off at startup, `MULTI_AGENT_LOCKED` | mode cannot be enabled, workflow routes → 403 |

`GET /api/attractions/modes` reports all four. The CI job runs with every
service disabled and asserts both the reported modes and the 403 responses,
which is the configuration required for the cloud deployment.

## Known limitations

- In the Reject example the Worker listed the only Sydney Culture attraction
  three times and the Reviewer still returned Pass; the human reviewer caught it.
  The Human Review step is the safeguard for this.
- The Planner runs on `qwen2.5:0.5b` and sometimes repeats criteria lines.
- A workflow takes about 85–105 seconds locally because Worker and Reviewer use
  `llama3.1:8b`.
