# Release 2 evidence reviews

Run these commands from the TripAgent repository root in the project Python
environment (`pip install -r agentic-loop/requirements.txt`). These are local,
non-containerised extensions of the existing collector/pipeline/prompt/report loop.
The structure follows [Lab 10](https://github.com/Georges034302/asd-labs/blob/main/Lab_10_Multi_Agent_Coordination.md)
and [Lab 11](https://github.com/Georges034302/asd-labs/blob/main/Lab_11_Testing_Deployment_and_Operations.md).

Existing individual modes remain available. Default `all` now runs eight modes,
including `multi-agent` and `testing`, for each selected feature. With no workflow
ID it selects the latest workflow by creation time for that feature; with no
manifest argument it uses `evidence/<feature>/manifest.json`. Missing evidence
is recorded, never silently passed. Explicit workflow/manifest overrides in
`all` require `--service` to prevent using one feature's evidence for another.
Individual `multi-agent` and `testing` modes still require `--service`.
Cloud deployment review is deferred.

## Multi-Agent Workflow Review

1. Run a workflow through the existing feature UI and record its workflow ID.
2. Review the three agent outputs and record Accept, Partially Accept (with a
   correction), or Reject in that UI.
3. Review the saved workflow from the terminal:

```powershell
python agentic-loop/core/orchestrator.py --mode multi-agent --service checklist --workflow-id "YOUR-WORKFLOW-ID" --checks-only
```

The collector reads `shared/multi-agent-server/workflow_state.sqlite3` in SQLite
read-only mode. `MULTI_AGENT_DB_PATH` or `--workflow-db "path/to/workflow.sqlite3"`
can select the server's actual database/a consistent SQLite backup. A database
inside a container must first be exported consistently, including committed WAL
data; do not copy just the main file of a live WAL database.

Checks include feature/ID, stage identities and successful nonempty outputs,
worker evidence, audit order, and matching human decision/status/audit records.
Reject is a valid recorded human decision, not a broken workflow. An undecided
workflow is PARTIAL. Invalid ordering or decisions are FAIL. No records are changed.
The original full input context is not stored by the coordinator, so complete
input-to-output factual verification is unavailable and appears as a limitation.

## Testing Report Review

Create a directory containing a JSON manifest and actual saved evidence files.
The manifest example below is a template, **not passing test evidence**. Replace
the commit, run ID and testcase names with the real values. Use the full SHA of
the code tested, not a later commit. The CI workflow already uploads Checklist
JUnit XML files in the `student-14582668-release2-tests` artifact.

To capture a fresh local pre-commit log in PowerShell:

```powershell
New-Item -ItemType Directory -Force evidence/checklist
pre-commit run --all-files --color never 2>&1 | Tee-Object -FilePath evidence/checklist/pre-commit.log
$scanExit = $LASTEXITCODE
$scanExit
git rev-parse HEAD
```

Keep that exit code and SHA in the manifest. Hooks can modify files: resolve
failures, commit the final changes, and collect scans/tests for the same version.
The collector accepts UTF-8 logs; on Windows PowerShell 5 use
`Get-Content evidence/checklist/pre-commit.log | Set-Content -Encoding UTF8 evidence/checklist/pre-commit-utf8.log`
and reference the UTF-8 file in the manifest.
Download and extract the CI artifact into this same evidence directory.
Inspect XML `testcase` attributes to obtain `classname::name` identifiers,
including parameter suffixes (e.g. `[Accept-completed]`).

```json
{
  "feature": "checklist",
  "commit": "REPLACE_WITH_FULL_40_CHARACTER_SHA",
  "pre_commit": {
    "commit": "REPLACE_WITH_SAME_SHA",
    "log": "pre-commit.log",
    "exit_code": 0
  },
  "ci": {
    "commit": "REPLACE_WITH_SAME_SHA",
    "workflow": ".github/workflows/student-14582668-ci.yml",
    "run_url": "https://github.com/Look0n/TripAgent/actions/runs/REPLACE_WITH_RUN_ID",
    "conclusion": "success",
    "junit": ["checklist-release2-endpoints.xml", "checklist-regression.xml"],
    "endpoints": [
      {
        "method": "POST",
        "path": "/api/checklist-items/multi-agent/workflow",
        "tests": ["tests.test_multi_agent_routes::test_start_uses_database_evidence"]
      },
      {
        "method": "POST",
        "path": "/api/checklist-items/multi-agent/workflow/<uuid>/review",
        "tests": ["tests.test_multi_agent_routes::test_decision_is_forwarded_without_database_changes[Accept-completed]"]
      }
    ]
  }
}
```

```powershell
python agentic-loop/core/orchestrator.py --mode testing --service checklist --evidence evidence/checklist/manifest.json --checks-only
```

By default the manifest and scan/CI commits must match current HEAD. To review
an older run intentionally, pass `--commit FULL_TESTED_SHA`; this is recorded in
the report. Local uncommitted changes are not covered by that commit's evidence.
Artifacts must be UTF-8, at most 2 MiB each, and inside the manifest directory.
Use separate directories per run rather than concatenating old scan logs.

The collector checks Ruff, detect-secrets and pip-audit hook summary lines,
exit code, matching feature/commit/workflow, CI conclusion/run URL, actual JUnit
testcases and mappings for at least two endpoint functions. Failures and errors
fail validation; skips/missing evidence cannot produce PASS. Raw error log
contents and secret scan findings are not sent to the models; artifact names, hashes and
structured outcomes are retained. Metadata/mappings are operator-supplied:
this does not authenticate a GitHub run or prove what an endpoint test covers.
Human review must verify those claims against the run and test source.

## Model review and results

First run `--checks-only` to inspect deterministic results without Ollama.
Then repeat the same command **without `--checks-only`** with Ollama and the
configured `qwen2.5:0.5b` and `llama3.1:8b` models available. The implementation
model assesses the evidence; the reviewer checks that assessment against the
same evidence using Strengths, Risk, Correction and Retest sections.

Each run writes unique JSON and Markdown files under
`docs/evidence/agentic-loop/runs/`. Execution completion, evidence validation and
model completion are reported separately. Exit 0 requires PASS and (unless
checks-only) successful model output checks. FAIL/PARTIAL/model failures return 1;
invalid CLI arguments return 2. A positive model opinion cannot override failed
checks. PASS means the implemented evidence checks passed within the stated
limitations, not a deployment approval. Human release approval remains separate.

Run regression tests with:

```powershell
python -m pytest agentic-loop/tests -q
```

## Temporary feature switches

The CLI enables MCP, RAG and Multi-Agent via existing backend mode APIs before
running each corresponding pipeline. It verifies ON and restores an originally
OFF switch in a finally block, including when the pipeline fails or is interrupted.
An originally ON switch stays ON. Default application settings are unchanged.
A locked, unavailable or unauthorised mode endpoint produces MODE_FAILED;
restoration failure produces MODE_RESTORE_FAILED and a terminal warning.
Do not run overlapping reviews or change UI switches during a review: these
switches are process-wide. Force-killing Python cannot execute its finally block;
restore the switches manually in that case.

Checklist uses POST, Account/Flight use PUT, and Accommodation Multi-Agent uses
POST. Attractions Multi-Agent uses PUT. Accommodation/Attractions MCP and RAG
are environment-controlled and have no runtime switch API; their configuration
is not rewritten. Their report records ENVIRONMENT_CONTROLLED. Account mode
APIs use the existing authorised LOOP_ACCOUNT_CUSTOMER_ID header contract.
Enabling a mode does not launch stopped servers, create workflows or fabricate
test evidence. Multi-Agent reviews saved workflow history; its human decision
must already exist for complete validation. RAG reviews still contact the shared
RAG service directly. Retrieval/grounding defects are not fixed by switching ON.

```powershell
# All eight review types for Checklist, with automatic evidence selection:
python agentic-loop/core/orchestrator.py --service checklist
# All eight review types for all five features:
python agentic-loop/core/orchestrator.py
# Select exact evidence for a Checklist all-mode run:
python agentic-loop/core/orchestrator.py --service checklist --workflow-id "YOUR-ID" --evidence evidence/checklist/manifest.json
```
