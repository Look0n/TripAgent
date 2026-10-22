# Release 2 Evidence — Flight Search Service

Student: Haris Naeem (25487036)
Feature: flight
Captured: 22 October 2026

## Environment

| Component | Where it runs | Port |
|---|---|---|
| flight-frontend / flight-backend / flight-database | Docker Compose | 3005 / 5005 / 6005 |
| Shared MCP Server | host, non-containerised | 7001 |
| Shared RAG Server | host, non-containerised | 7002 |
| Shared Multi-Agent Server | host, non-containerised | 7003 |
| Planner model | Ollama | qwen2.5:0.5b |
| Worker and Reviewer model | Ollama | llama3.1:8b |

The containerised flight backend reaches all three non-containerised shared
services through `host.docker.internal` with an `extra_hosts: host-gateway`
mapping declared in `docker-compose.yml`.

## Evidence index

| File | Shows | Criterion |
|---|---|---|
| `multi-agent-terminal.log` | Planner → Worker → Reviewer → Human Review executed through the flight backend/API from the terminal, including workflow history and human-review validation | 2 |
| `multi-agent-ui-1-panel.jpg` | Multi-Agent panel on the flight search page, reached through the shared frontend | 2 |
| `multi-agent-ui-2-planner-worker.jpg` | Planner plan and Worker recommendation rendered in the frontend | 2 |
| `multi-agent-ui-3-evidence-review.jpg` | Flight records supplied to the agents, Reviewer verdict against that evidence, and the pending human review decision | 2 |
| `multi-agent-ui-4-decision-history.jpg` | Recorded human decision with correction, and the workflow history table | 2 |

## Multi-Agent design notes

Evidence is retrieved by the flight backend from the flight database service
over HTTP and passed to the agents as `context.evidence` with
`constraints.evidence_only = true`. The Worker prompt forbids inventing
airlines, routes, departure times, prices or seat counts, and the Reviewer
checks that every recommended flight exists in that evidence set. In the
captured workflow the Worker selected flight_id 2 (Jetstar, 109.0), the lowest
priced record in the supplied evidence, and the Reviewer returned
Evidence check: Pass, Constraint check: Pass, Recommendation: Accept.

Multi-Agent mode is disabled on backend startup and can be forced off by
deployment configuration through `MULTI_AGENT_LOCKED`, which is how the
Multi-Agent Server is kept disabled by default in the cloud deployment.

## Known limitation

The Planner runs on `qwen2.5:0.5b`, the smallest configured model, and its
criteria list repeats several near-identical lines. The Planner output is an
instruction to the Worker rather than user-facing content, and the Worker and
Reviewer both run on `llama3.1:8b`. Raising the Planner to the larger model
would resolve the repetition at the cost of workflow latency.
