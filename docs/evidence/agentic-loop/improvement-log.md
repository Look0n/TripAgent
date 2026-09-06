# DB prompt validation - 2026-09-06

## Architecture implementation and validation - 2026-09-06

Implemented Lab-style file/Compose evidence collection and implementation/review prompt flow. TripAgent adaptations include explicit Flask/Nginx frontend contracts, normalized Compose JSON, a shared project snapshot, scoped environment checks, and separate configuration/runtime/model statuses. No application, Compose, Dockerfile, gateway, or workflow files were modified.

- Initial run: runs/architecture-20260906T070005Z-e8b3a56f.json. All five configuration checks passed. Attractions frontend was running but unhealthy; its runtime validation failed.
- Added explicit shared service/network checks and PARTIAL handling for configured-but-unreported container health. This is configuration evidence, not proof of network requests succeeding.
- Final checks-only run: runs/architecture-20260906T070227Z-05e31a93.json. All five configuration results passed; Attractions runtime remained FAIL because attractions-frontend was unhealthy. Account, Accommodation, Checklist and Flight runtime checks passed. No automatic repair or restart was attempted.
- Live Checklist models: runs/architecture-20260906T070209Z-e0596988.json. Both Qwen and Llama calls completed and both word limits passed. Qwen alleged inconsistent shared configurations without a FAIL finding. Llama stated that configuration was consistent and no changes were needed, but used an ambiguous Approved label rather than explicitly rejecting the proposal. Human review rejects the implementation recommendation; model-quality limitations remain unresolved. No recommended changes were applied.

Validation used real Compose configuration and in-memory fixture changes for incorrect database URLs, build paths, volumes, isolated networks, unavailable/stopped runtime, and secret filtering. Also checked syntax, absence of new code comments, prompt rendering, checks-only mode, failure gates, and preservation of deterministic validation status during model review. These fixture checks did not modify real services or create mock live reports.

Not verified: browser/authenticated gateway flows, inter-service HTTP communication, CRUD, restart persistence, runtime image freshness, full Nginx configuration syntax, CI/CD, or user AI-mode. Database path defaults are explicitly unverified where DATABASE_PATH is not set in Compose.

## Endpoints implementation and validation - 2026-09-06

Lab 04 live HTTP collection and Lab 05 mode/prompt orchestration were adapted to explicit TripAgent GET contracts. No application records were created, updated, or deleted. No student service, Compose, or workflow files were changed.

- Initial run: runs/endpoints-20260906T064254Z-85d9a42b.json. Two health assertions were wrong because Accommodation and Attractions return status=ok, not healthy. Corrected the collector configuration against their actual app.py contracts; these were test-configuration defects, not service defects.
- Corrected HTTP run: runs/endpoints-20260906T064402Z-7fb13e83.json. All 22 configured checks passed: Account 4, Accommodation 4, Attractions 4, Checklist 5, Flight 5. Account coverage is unauthenticated session/protection only. CRUD writes, authenticated access, gateway/frontend integration, and user AI-mode were not tested.
- Prompt integration failure: runs/endpoints-20260906T064408Z-8245af62.json. The existing renderer incorrectly treated nested JSON closing braces as an unresolved placeholder. Changed validation to inspect template syntax before substituting data. Verified DB and Endpoints template compatibility.
- Live model run: runs/endpoints-20260906T064524Z-ce5bc082.json. Checklist HTTP checks passed and Qwen/Llama calls completed. Qwen incorrectly proposed returning 200 for all requests; Llama rejected the interpretation because invalid input correctly returns 400. Both word limits passed. Human review rejects the implementation recommendation. No proposed changes were applied.

Mock checks covered missing responses versus HTTP failures, expected 401/400, malformed/oversized JSON, timeouts, empty-list PARTIAL results, placeholder handling, model failure gates, and checks-only mode. Mock results were not saved as live evidence. The transport test fixture initially used a plain dictionary for HTTP headers; corrected the fixture to email.message.Message to match urllib responses.

Execution status, HTTP validation status, and model status are separate. A completed model call is not proof of recommendation correctness. The model-quality limitation remains open.

## Scope

Checklist only. Live read-only SQLite evidence: 10 checklist_items rows, zero invalid rows under the collector checks, zero reported foreign-key violations. Qwen 2.5 0.5B generated recommendations; Llama 3.1 8B reviewed them. No suggested database changes were applied.

## Before

Run: runs/db-20260906T060453Z-1304cf8e.json

Both model calls completed. Qwen incorrectly claimed that 10 rows was below the minimum of 10 and proposed adding an existing table. Llama rejected the proposal, but exceeded the 35-word review limit.

## Adaptation

Clarified that count >= 10 passes, that collector PASS findings must not be converted into defects, and that an all-pass result should use the no-improvement response. Strengthened the review's total word limit. These were prompt changes, not database changes.

## After

Run: runs/db-20260906T060527Z-c1db4173.json

Both model calls completed and both word limits passed. Semantic validation still FAILED: Qwen again called 10 rows defective and proposed an unsupported foreign key on is_completed. Llama stated that 10 rows passes but approved without addressing the unsupported constraint. Human review rejects both outputs as a reliable recommendation/review pair.

## Conclusion and next check

Pipeline connectivity, evidence forwarding, error reporting, and report persistence were verified. Recommendation quality was NOT validated. COMPLETED denotes successful execution, not human approval or application correctness. Do not apply these recommendations. A next experiment can use a stronger approved implementation model already available through Ollama, with the same evidence and a review prompt explicitly checking every proposed change. Model changes require a separate agreed step.

## Environment failures preserved

- runs/db-20260906T060259Z-a26a8e3f.json: sandbox access failure before model calls.
- runs/db-20260906T060314Z-6bc99ff0.json: checklist-database was not running; no model calls.

Mock checks separately covered missing/empty prompts, unresolved placeholders, invalid/empty model responses, HTTP/connection/timeouts, stage failure gates, shared review evidence, and unique report filenames. Mock responses were not saved as live evidence.

## DevOps implementation and validation - 2026-09-06

Checklist ports are frontend 3004, backend 5004 and database 6004. Application defaults, Dockerfiles and Compose already matched. Corrected three remaining Checklist workflow references: backend publish mapping, backend health URL and frontend browser API URL. Other students' workflows and shared Compose were not modified.

DevOps follows the Lab05 observation, implementation recommendation, review and human adaptation pattern. It reads local workflow declarations and existing GitHub run/job/step/artifact metadata. It does not dispatch workflows, execute workflow shell commands, download artifact contents, or apply model recommendations. Existing ci_pipeline service mappings are reused for all five services.

Added PyYAML 6.0.2 for YAML parsing. BaseLoader preserves the GitHub Actions on key. The collector distinguishes CI status, evidence completeness and local revision differences. An offline run is PARTIAL, not a passing CI execution. A successful historical run does not validate a dirty working tree. Missing artifacts are evidence gaps, not failed jobs. Exit code 1 can therefore indicate incomplete evidence as well as failure.

Validation evidence:

- runs/devops-20260906T073237Z-bb9a1ae3.json: all five local workflows parsed successfully; offline CI status NOT_CHECKED and validation PARTIAL. Flight workflow path filters reference student-5.yml rather than its current workflow filename; warning only, not changed.
- runs/devops-20260906T073254Z-6c9e0e18.json: actual Checklist run 33959538620, attempt 1, failed at Wait for Checklist backend. Subsequent frontend/CRUD/AI validation steps were skipped. Local workflow differs from the workflow at that run's head SHA.
- runs/devops-20260906T073504Z-4bb640de.json: actual Qwen implementation and Llama review calls both completed. Qwen invented an ai_endpoint pytest fixture recommendation; Llama repeated it and exceeded 35 words. Human review rejects this recommendation. No suggested workflow changes were applied.
- runs/devops-20260906T074513Z-5f531fab.json: existing main-branch runs fetched for all five services. Account, Accommodation, Attractions and Flight had successful historical CI runs; Checklist failed. All remain non-PASS for current local validation because of local changes and/or missing evidence. Flight artifact metadata was available; artifact contents were not inspected.

In-memory checks passed for Python syntax, YAML on handling, invalid YAML, unavailable GitHub API, wrong-workflow run selection, shared evidence in both model prompts, model error propagation, a matching successful run, dirty-worktree safeguards and pagination limits. Mock evidence was not stored as actual CI evidence. git diff --check passed with line-ending warnings only.

Run from the TripAgent-demo repository root:

```powershell
python -m pip install -r agentic-loop/requirements.txt
python agentic-loop/core/orchestrator.py --mode devops
python agentic-loop/core/orchestrator.py --mode devops --service checklist
```

These commands select the latest existing run on main for each selected workflow. Both commands include Ollama implementation and review calls. They do not execute a new CI run. Public GitHub reads need no token unless access/rate limits require GH_TOKEN or GITHUB_TOKEN; tokens are not written to reports.

Remaining work: commit/push and rerun the corrected Checklist CI with user authorization, inspect actual artifact/log contents where available, and improve/retest model grounding. The current collector is metadata-based evidence collection, not full Lab05 artifact-content verification or proof that Release 0 is complete.

## CLI simplification and Release 0 audit - 2026-09-06

Removed public CLI flags --db-only, --checks-only, --offline, --run-id and --branch from orchestrator.py at the user's request. Retained --mode, --service and argparse help. These removed flags are not present in the inspected Lab03, Lab04 or Lab05 source, and are not required by the supplied project specification. Internal collector/pipeline parameters remain available for diagnostic testing; normal CLI execution always includes the model stages after usable evidence is collected. Existing reports are preserved.

Syntax and in-memory dispatch tests passed for all four modes, single-service selection, all-five DevOps default selection and rejection of removed flags. No live CI or LLM execution was performed for this CLI-only verification.

Compliance assessment is based on saved evidence, not a fresh live release certification:

- DB report db-20260906T061646Z-d5278f00.json: Attractions reviews table has 5 rows, below the specification's 10-record minimum. Other four service collection stages passed. Multiple model recommendations contradict valid row counts.
- Endpoints report endpoints-20260906T065239Z-842e7573.json: all five GET-only validation scopes passed. CRUD writes, authenticated flows and browser/AI integration were not tested by this collector. Several recommendations misinterpret expected 400/401 responses.
- Architecture report architecture-20260906T071942Z-f95f8868.json: four deterministic scopes passed; Attractions frontend was unhealthy. Account model call timed out. Several other model recommendations contradict passing configuration evidence.
- DevOps report devops-20260906T092614Z-9e056573.json: Checklist historical CI failed, other historical CI runs succeeded; local overall validation is FAIL or PARTIAL. Artifact contents remain unverified. Several recommendations confuse missing evidence with workflow failure.

The four review modes follow the Lab04/05 modular collector-pipeline-prompt-orchestrator structure. They are engineering review targets, not four independently specified Release 0 acceptance gates. Lab05 additionally demonstrates artifact report-content checks and a recorded prompt-change/rerun decision cycle; current DevOps metadata collection does not fully reproduce that evidence workflow. Lab05 DevOps uses 30-word responses whereas this project's prompts use 60/35; this is a local adaptation, not a specification requirement.

Specification sections 4.2, 4.3 and 6.2.1 still require application AI-mode, the frontend/backend/Ollama/LLM interaction and a demonstrated shared Plan-Act-Observe-Adapt workflow. A fifth CLI user-AI review mode is not prescribed, but the four engineering review modes alone cannot prove application AI-mode compliance. Report template section 11 requires the integrated application's Plan, Act, Observe and Adapt explanation. Do not remove application AI routes or UI.

Priorities are to resolve actual service failures, rerun the corrected Checklist CI, obtain inspectable CI evidence, and document human review plus adaptation/retest. A reliable human decision is required; model completion or an Approved response is not release acceptance. Workflow filenames also differ from the specification's student-1.yml through student-5.yml convention; confirm the team's student-ID naming with the tutor rather than renaming shared files silently.

Sources: supplied ASD_2026_Project_Specifications.pdf sections 2.2, 4.2-4.6, 6.2.1, 7.3 and Release 0 submissions; supplied technical report template section 11; official asd-labs Lab04 architecture/modular loop and Lab05 sections 6-8.
