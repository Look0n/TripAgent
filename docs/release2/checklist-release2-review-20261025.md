# Checklist Release 2 specification review

Review date: 25 October 2026 (Australia/Sydney).

Scope: current local TripAgent checkout, including the uncommitted Checklist
ON/OFF implementation. Base commit: `842d2a9`. This review does not establish
the state of a newer remote branch or a deployed cloud application.

Source: `Ass3_specification.pdf`, especially pages 3-9. The specification requires
two assigned backend endpoint functions to be tested through the student's
workflow, local pre-commit security scans, non-containerised local AI services,
group cloud deployment with AI features disabled by default, and review evidence.

## Findings

| Requirement | Current evidence | Result / remaining work |
| --- | --- | --- |
| Retain Checklist frontend, backend, database and CRUD | Existing services, CRUD routes and regression tests; CI retains Docker build and CRUD smoke steps | Implemented; current Docker execution not reverified because the engine is stopped |
| Retain local AI, MCP and RAG integration | Existing recommendation, MCP and RAG routes remain registered | Code retained; real local AI execution and UI demonstration need separate evidence |
| Shared non-containerised Multi-Agent server | Shared Flask server and terminal runner; backend HTTP client and Checklist UI | Integration implemented; no AI container is added by this CI change |
| Planner -> Worker -> Reviewer -> human review | Coordinator calls stages sequentially; three Checklist prompts; decision routes and UI | Implemented in code; actual model execution/history/audit evidence is still required |
| Application evidence supplied to Worker | `checklist_context.py` reads database API records and calculates summary counts | Tested with controlled database responses; no invented client context is accepted |
| Human approval, partial acceptance, rejection | Partial acceptance requires a comment; shared coordinator records decisions and terminal states | Implemented. Decision recording does not write Checklist items, which is consistent with a review-only workflow |
| Two post-commit backend endpoint functions | Explicit Release 2 pytest step in `.github/workflows/student-14582668-ci.yml` | Configured and locally tested; successful GitHub run evidence remains pending |
| Local pre-commit security scans | Repository config contains Ruff security rules, detect-secrets and pip-audit | Local `.git/hooks/pre-commit` was absent during inspection; install/execute scans and retain real results. This review is not a security-scan report |
| Release 2 agentic-loop review modes | Current CLI lists db/endpoints/architecture/devops/mcp/rag/all | Multi-Agent Workflow Review, Testing Report Review and Cloud Deployment Report Review modes were not found in this checkout |
| Cloud AI-disabled baseline | MCP/RAG have environment gates; Multi-Agent defaults OFF and supports a lock | Incomplete: `/api/checklist-items/recommend` has no explicit OFF gate. An unreachable Ollama URL is not equivalent to disabling AI |
| Group cloud workflow and scripts | Cloud Nginx template and gateway Dockerfile exist | `.github/workflows/cloud-deployment.yml` is absent in this checkout; successful group deployment and associated evidence are not verified |
| Release 2 report/evidence | Existing evidence includes other features and earlier agentic-loop runs | Checklist-specific live workflow, pre-commit, hosted CI, cloud and new agentic-loop reports/logs must be collected |

## Required endpoint tests

Both functions are in `student-14582668/checklist-backend/routes/multi_agent_routes.py`.

1. `POST /api/checklist-items/multi-agent/workflow` -> `start_workflow`
   - valid request produces HTTP 202 and forwards database-derived context;
   - feature is fixed to Checklist; client-supplied context is not trusted;
   - invalid requests fail before database or agent requests;
   - database connection/malformed evidence/oversized evidence errors are handled;
   - OFF and locked modes prevent execution.
2. `POST /api/checklist-items/multi-agent/workflow/<uuid>/review` -> `review_workflow`
   - all three human decisions and comments are forwarded;
   - partial acceptance without a correction is rejected;
   - invalid decisions/corrections and mismatched workflow responses are rejected;
   - upstream conflict responses are propagated;
   - Checklist database write methods are guarded against accidental calls.

Dependencies are mocked. These tests validate the Checklist endpoints and their
contracts, not actual LLM quality, shared coordinator persistence, concurrent
approval behaviour, or browser interaction. The existing conflict test simulates
an upstream 409; it does not itself execute the coordinator's transition logic.

## Workflow changes

- Preserve the assigned filename and existing CRUD/build validation.
- Add shared AI service paths to push/pull-request triggers and manual dispatch.
- Add JavaScript syntax checks and shared Multi-Agent Python syntax checks.
- Run the Release 2 endpoint suite separately from the existing regression suite,
  without duplicating the endpoint tests in the regression run.
- Save JUnit XML and pytest logs as `student-14582668-release2-tests`.
- Start the isolated CI backend with MCP/RAG disabled and Multi-Agent locked OFF.
- Check disabled status, blocked workflow calls and rejected attempts to enable
  Multi-Agent in the locked CI container.
- Check that the served frontend includes the toggle/review form and valid JS.
- Collect container logs before cleanup, including on failure.
- Record the two endpoint mappings and evidence limitations in the Actions summary.
- Keep local pre-commit scanning separate; CI is not evidence of a local commit hook.
- Do not add cloud deployment to the individual workflow or claim that CI deploys.

## Validation performed

- All Checklist backend tests: **117 passed** (36 Multi-Agent tests and 81 regression tests).
- YAML parsing: passed; push, pull_request and workflow_dispatch triggers present.
- Bash syntax: all 24 `run` scripts passed `bash -n`.
- Embedded Python: the disabled-feature smoke script parsed successfully.
- Python source parsing, JavaScript syntax and `docker compose config --quiet`: passed.
- Docker build/container smoke execution: **not run**, Docker engine unavailable.
- GitHub Actions execution, cloud deployment, live Ollama and browser interaction:
  **not run** in this review.

## Remaining submission work

1. Add and test an explicit AI recommendation OFF gate, then configure all four
   AI integrations OFF in the group cloud deployment.
2. Complete/verify the three Release 2 agentic-loop review modes with the team.
3. Install/run the required local pre-commit hooks and retain scan outputs.
4. Commit the endpoint tests, workflow and the ON/OFF code together when ready;
   the updated workflow relies on the `/multi-agent/mode` route and UI button.
5. Push and download actual Actions artifacts. Record run URL, commit SHA,
   endpoint mappings, pass/fail totals and failures/fixes in the testing report.
6. Demonstrate real local Multi-Agent processing and all human decisions; export
   the corresponding history/audit evidence.
7. Verify group cloud-deployment workflow, core CRUD, AI-disabled defaults and
   deployment logs, then run the required agentic-loop report reviews.

No commit, push, cloud deployment, or application-source changes were made as
part of this CI review. Previously requested ON/OFF changes remain in the working tree.
