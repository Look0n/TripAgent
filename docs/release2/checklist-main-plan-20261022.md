# 최신 main 기준 Checklist / Agentic Loop Release 2 계획

확인일: 2026-10-22 (Australia/Sydney).
원격 main SHA: e7fc4120a1141ade47c00ac49c6f4deea9857cec.
커밋: Improve multi-agent worker model, 2026-10-21T06:18:04Z.
분석은 GitHub에서 해당 SHA에 고정하여 읽은 코드 기준이다. 로컬 HEAD df7f6c2a8f797008dc6ea7dba97c9dda279bf9b6과 다르며 pull/reset하지 않았다.
이 문서는 2026-10-21 계획의 현재 상태와 구현 순서를 대체한다. 기능 코드 수정/테스트 실행/배포는 하지 않았다.

## 1. 기존 계획에서 달라진 점

| 항목 | 최신 main에서 확인한 상태 | 앞으로 할 일 |
|---|---|---|
| 공용 Multi-Agent | shared/multi-agent-server 이미 존재, 기본 7003 | 신규 구축 대신 Checklist 연결 |
| Agent 순서 | Planner → Worker → Reviewer, plan/context 실제 전달 | 순서 재구현 불필요, 테스트/근거 검증 보강 |
| 비동기 실행 | POST /workflow가 202, thread pool 작업, GET polling | Checklist UI도 동일 계약 사용 |
| Human Review | Accept/Partially Accept/Reject, partial correction 필수, 중복 review 409 | Checklist proxy/UI 연결 |
| 저장 | workflow_state.sqlite3의 workflows/audit | JSONL로 교체하지 않고 export 추가 |
| 모델 | Planner Qwen, Worker/Reviewer Llama | 현재 설정 유지, 측정 후 팀과 조정 |
| feature prompt | Account/Accommodation 있음 | checklist_planner/worker/reviewer.txt 추가 |
| Checklist | CRUD/AI/MCP/RAG 및 테스트 존재 | Multi-Agent client/routes/UI/env 없음 |
| 공용 loop | db/endpoints/architecture/devops/mcp/rag/all | multi_agent/testing/deployment 추가 |
| loop reporter | MCP/RAG JSON+Markdown, SHA/dirty, sanitise, checks-only | 이 패턴 확장 |
| pre-commit | Ruff S, detect-secrets, pip-audit 등 이미 설정 | 설치/실행 증거, dependency 검사 범위 확인 |
| cloud 배포 | 조회 tree에 cloud-deployment.yml/배포 scripts 없음 | 팀 공용 작업으로 추가 |

주요 소스:
- https://github.com/Look0n/TripAgent/blob/e7fc4120a1141ade47c00ac49c6f4deea9857cec/shared/multi-agent-server/coordinator.py
- https://github.com/Look0n/TripAgent/blob/e7fc4120a1141ade47c00ac49c6f4deea9857cec/shared/multi-agent-server/app.py
- https://github.com/Look0n/TripAgent/blob/e7fc4120a1141ade47c00ac49c6f4deea9857cec/agentic-loop/core/orchestrator.py
- https://github.com/Look0n/TripAgent/blob/e7fc4120a1141ade47c00ac49c6f4deea9857cec/.pre-commit-config.yaml

## 2. Checklist 목표와 범위

첫 완성 목표: 실제 checklist 기록을 바탕으로 준비 상태를 검토하고 추가 준비 사항을 제안한 뒤, 사람이 승인/부분 승인/거절하는 전체 흐름.

브라우저 → 기존 gateway → Checklist backend → 공용 Multi-Agent :7003 → Planner → Worker → Reviewer → polling 결과 → 사람 review.

첫 버전은 read-only 분석 및 결정 기록이다. 승인 즉시 DB가 변경된다고 표시하지 않는다. 추천 자동 적용은 후속 선택 기능으로 분리한다. 이미 있는 AI 추천/추가 기능과 Multi-Agent review를 각각 유지한다.

### 개인 backend

신규 파일:
- student-14582668/checklist-backend/services/multi_agent_client.py
- student-14582668/checklist-backend/services/checklist_context.py
- student-14582668/checklist-backend/routes/multi_agent_routes.py
- student-14582668/checklist-backend/tests/test_multi_agent_routes.py
- student-14582668/checklist-backend/tests/test_multi_agent_client.py

app.py에서 blueprint 등록. client는 Account의 작은 call_server/custom exception/X-Multi-Agent-Key 패턴을 참고하고, 기존 Checklist RAG client처럼 JSON 객체·timeout·응답 검증을 보강한다. Accommodation client에는 API key 전송이 없어 그대로 복사하지 않는다.

제안 backend prefix: /api/checklist-items/multi-agent

| Method/path | 기능 | 공용 API |
|---|---|---|
| GET /status | enabled/available 확인 | /health 및 필요 시 /workflow/status?feature=checklist |
| POST /workflow | DB 근거 수집 후 비동기 작업 제출, 202 반환 | POST /workflow |
| GET /workflow/<id> | 진행 상태/결과 조회 | GET /workflow/<id>?feature=checklist |
| POST /workflow/<id>/review | 사람 결정 전달 | POST /workflow/<id>/review |

기존 공용 API는 /review이다. 이전 계획의 /decision을 새로 만들 필요가 없다.
브라우저에는 user_request만 받고 feature와 evidence는 backend가 만든다. 입력은 JSON object, 1-4000자 문자열, decision enum, correction 타입/길이를 검증한다. 공용 404/409 등 의미 있는 상태를 보존한다.

### 실제 근거 만들기

database_api.get_checklist_items()로 조회하여 허용 필드만 context.evidence에 담는다. item_id/title/item_type/category/description/priority/is_completed 및 source/captured_at/누락 여부를 명시한다.
총 항목/완료/미완료/High 미완료 수는 Python으로 계산한다. 숫자 계산은 모델에게 맡기지 않는다.
공용 context 제한 20 KB에 맞춰 필드 길이·개수를 제한하고, 잘린 경우 total/used/truncated를 기록한다. 빈 목록은 DB 장애와 구분한다.
첫 연결은 DB 근거만 사용한다. RAG는 실패 원인 수정 후 출처와 함께 추가한다. 모델이 읽은 RAG 답변 자체를 사실의 근거로 대신 쓰지 않는다.

### Checklist 전용 prompt 세 개

shared/multi-agent-server/prompts/features/ 아래 추가:
- checklist_planner.txt: 준비 상태/우선순위/빠진 조건 확인 계획. 없는 목적지·날짜·취향을 만들지 않음.
- checklist_worker.txt: 제공한 checklist 근거로 결과 작성. 기존 미완료 항목과 새 추천을 구분. 추천은 최대 5개, task/packing 및 High/Medium/Low 범위.
- checklist_reviewer.txt: plan/evidence 일치, 중복/미지원 주장, 누락 조건, correction/retest 검토.

현 worker.output은 문자열이다. 첫 버전은 제목별 텍스트 결과로 표시한다. 실제 항목 추가가 필요하면 별도로 suggestions JSON 계약과 서버 검증을 추가한다. 문장을 임의 파싱해서 DB에 저장하지 않는다.
공용 common.py가 feature prompt를 이미 읽으므로 agent 파일을 Checklist 전용으로 복제하지 않는다.

### UI와 배포 설정

- 기존 checklist.html에 Multi-Agent section, 별도 multi_agent.js에 start/poll/render/review 함수를 둔다. 기존 apiRequest/makeElement/textContent 패턴을 재사용한다.
- 상태: queued → running → pending_review → completed/rejected, 또는 failed.
- 1-2초 간격의 중복 없는 polling, 최대 대기시간, 페이지 이동 시 중단, 재조회 지원. 브라우저 polling 중단을 서버 작업 취소라고 표시하지 않는다.
- pending_review에서만 review 버튼 활성화. Partial이면 correction 필수. 승인 후 DB 저장 완료라고 표시하지 않는다.
- checklist-backend Compose에 MULTI_AGENT_SERVICE_URL=http://host.docker.internal:7003, MULTI_AGENT_API_KEY, 명시적 ENABLED/LOCKED 설정 추가.
- 프로세스 전역 토글을 그대로 복사하지 않는다. 최소 버전은 배포 환경변수로 활성화/잠금을 결정하고 UI는 이를 표시한다.
- 공용 서버는 비컨테이너 로컬 실행 유지. Dockerfile이 있다는 사실만으로 현재 Compose에서 실행된다고 판단하지 않는다. 현재 Compose에는 Multi-Agent service가 없다.
- 기존 gateway는 /api/checklist-items/<path>를 이미 전달하므로 새 proxy route는 원칙적으로 불필요. 비동기 202/짧은 조회 요청을 쓰면 모델 전체 시간을 기다리도록 30초 gateway timeout을 늘릴 필요가 없다.
- AI 추천 route에 AI_ENABLED 차단도 추가한다. 현재는 모델 URL을 끊는 것만으로 명시적 OFF가 되지 않는다. cloud baseline에서 AI/MCP/RAG/Multi-Agent OFF를 backend와 UI 모두 확인한다.

## 3. 공용 서버에서 필요한 작은 보완

1. 증거 보존/export: 현재 payload는 원본 context 전체를 보존하지 않고 worker 결과에 evidence 배열만 남긴다. 실행에 사용한 context snapshot과 출처/시각/요약을 크기 제한·민감정보 제거 후 저장한다. workflow+audit를 조회/내보내는 명시적 기능을 추가한다. JSON/JSONL은 제출용 export이며 SQLite 저장을 교체하지 않는다.
2. 요청 검증: app.py에서 JSON 배열/문자열에 .get을 호출하지 않도록 dict 검사를 먼저 한다. 비정상 입력은 400.
3. 모델 결과: 빈 응답을 성공으로 처리하지 않도록 검사한다. timeout은 현재 함수가 반환된 뒤 경과시간을 비교하므로 즉시 중단 장치가 아니다. Ollama HTTP timeout과 단계별 기록을 정렬한다.
4. 재시작: SQLite에는 queued/running이 남지만 executor 작업은 재개되지 않는다. 재시작 시 interrupted/failed 처리 또는 명시적 재실행 정책을 정한다. UI의 무한 polling을 막는다.
5. MAX_WORKFLOWS는 thread 개수 제한이며 대기열 제한이 아니다. 시연 규모를 넘어 동시 요청을 받을 때 queue cap/중복 제출 방지를 추가한다.
6. 현재 feature별 조회는 사용자별 소유권 검사와 다르다. 개인별 privacy를 주장하려면 gateway의 trusted user와 workflow 소유권을 연결해야 한다. 그렇지 않으면 공용 Checklist 데모 범위를 명시한다.

1-4는 새 loop의 신뢰할 수 있는 증거·실패 검증에 직접 필요하다. Account/Accommodation 호출 계약은 유지하고 팀과 변경 범위를 공유한다.

## 4. Agentic loop 계획

현재 MCP/RAG collector/pipeline/reporter를 출발점으로 삼는다. 기존 six modes를 보존한다.

| 새 mode | collector 입력 | 판단 |
|---|---|---|
| multi_agent | 실제 workflow/export/audit, feature prompt, API 결과 | 세 단계 순서, plan/evidence 전달, nonempty output, 실패 상태, 사람 review, 재승인 차단 |
| testing | pre-commit 결과 + 해당 SHA의 개인 CI/JUnit/endpoint 결과 | 보안 scan 실행 여부, endpoint 2개 실측, 실패/누락/오래된 결과 |
| deployment | 배포 보고서 + cloud workflow + smoke | 통합 UI/CRUD, 이미지/SHA, AI 4종 OFF, 영속성/복구, release 결정 |

추가: collectors/{multi_agent,testing,deployment}_collector.py 및 pipelines/{multi_agent,testing,deployment}_pipeline.py. 필요하면 testing collector 내부에서 pre/post 함수를 나눈다. Lab 11의 두 검사 흐름을 과제의 Testing Review 결과로 종합한다.
수정: review_config.py, services.py, orchestrator.py, reporter.py, prompts/service/implementation 및 review, loop tests.

재사용 원칙:
- core.validation.check/finish/sanitise, validation_passed 유지.
- execution_status/validation_status/model_status를 분리한다. LLM 평가로 실제 FAIL을 PASS로 덮지 않는다.
- 신규 모드에도 --checks-only를 허용하고 '모델 검토 생략'을 보고서에 표시한다.
- 실제 사람이 내린 review 기록을 읽는다. collector가 Accept를 자동 제출하여 human evidence를 만들지 않는다. 자동 테스트 fixture는 별도 표기한다.
- report에는 inspected workflow_id, evidence timestamp, code SHA, CI SHA, model/prompt, limitations를 저장한다. source를 일괄 live-services로 쓰지 않고 saved-audit/ci-artifact/cloud-probe 등 실제 출처에 맞춘다.
- all 모드는 외부 cloud 증거가 없는 로컬 실행에서 의미를 명확히 한다. 미실행을 PASS로 표시하지 않고 기존 동작을 유지하거나 release 모드를 명시적으로 선택한다.

### 기존 결과를 먼저 정리할 이유

저장된 2026-10-04 보고서는 현재 SHA의 재검증 결과가 아니다.
- Checklist MCP: Validation PASS지만 모델 출력이 매우 길게 반복되고 리뷰가 유효하지 않다. Models COMPLETED는 품질 통과를 의미하지 않는다.
- Checklist RAG: checklist_item_types:reference_hit, checklist_unsupported:answer_contract가 FAIL.
- ai_runner.py는 temperature만 설정하고 num_predict 출력 상한을 두지 않는다. 근거 요약/길이 제한, 모델 출력 상한, 형식·반복 결과 검사 후 재실행한다.

따라서 P0에서 기존 --mode mcp/rag --service checklist --checks-only로 현재 상태를 재현하고, 이어 모델 포함 실행 결과를 확인한다. MCP/RAG 모드를 새로 구현하는 작업은 하지 않는다.

## 5. Testing / CI / Cloud

- .pre-commit-config.yaml은 이미 있다. 새 파일을 중복 생성하지 않고 실제 hook 설치와 commit 시 scan 결과를 남긴다. pip-audit가 각 서비스 requirements를 어떻게 전달받는지 확인하고, Checklist FE/BE/DB와 공용 서버의 전체 dependency 집합이 명시적으로 검사되도록 보강한다.
- 개인 CI는 이미 pytest+Docker+CRUD smoke를 수행한다. GET 목록과 POST 생성 두 endpoint를 명확한 pytest integration test로 식별하고 실제 backend를 호출한다. 필터/응답 schema/잘못된 payload/생성 후 재조회까지 검증한다.
- unit tests는 모델/HTTP를 mock할 수 있지만 실제 endpoint 증거와 분리한다. --junitxml, scan report, CI run URL/SHA, 실행시간을 artifact로 저장한다.
- .github/workflows/student-14582668-ci.yml paths에 새로 의존하는 shared/multi-agent-server와 필요한 공통 경로를 반영하고 공용 loop 테스트 workflow도 마련한다.
- CI의 AI/MCP/RAG/Multi-Agent OFF를 명시한다. 기존 AI 빈 입력 400 검사는 OFF 403 정책 도입 후 목적에 맞게 분리하여 수정한다.
- 조회된 최근 Checklist CI 성공은 79f08f3 커밋의 run 39175768269다. 최신 e7fc412에서 Account/Accommodation은 성공했으나 이를 Checklist 최신 검증으로 부르지 않는다.
- cloud-deployment.yml과 실제 배포 scripts는 팀 공용 담당 작업. Azure/AWS는 팀 결정에 맞춘다. 원격 tree만으로 외부 클라우드 리소스 존재 여부는 판단할 수 없다.
- 다른 서비스의 OLLAMA_URL=http://ollama 설정이 남아 있어 비컨테이너 로컬 통합 주소를 함께 점검한다. cloud 기본값과 local 설정을 분리한다.

## 6. 구현 순서 및 완료 조건

| 순서 | 작업 | 완료 기준 |
|---|---|---|
| P0 | 최신 main 기반 작업 checkout, 기존 MCP/RAG 검증 재현 | SHA 기록, 남은 실패 목록, 기존 동작 기준선 |
| P1 | Checklist context/client/routes + feature prompt 3개 | 실제 DB 근거로 202 제출, polling, pending_review, review 완료 |
| P2 | Checklist UI + env/AI OFF | 로그인한 통합 UI에서 정상/실패/승인/거절 시연 |
| P3 | 공용 evidence export/실패 보완 + multi_agent loop | 실제 사람 review가 포함된 재현 가능한 보고서 |
| P4 | pre-commit 실측 + CI endpoint 증거 + testing loop | 동일 버전의 scan/두 endpoint/모델 검토 및 수정·재검증 기록 |
| P5 | 통합 cloud 및 deployment loop | cloud CRUD/AI OFF, 배포 로그, 사람 release decision |

P1 첫 목표는 '추천 자동 저장'이 아니라 '현재 Checklist 상태를 세 agent가 검토하고 사용자가 판단한 기록이 남는 것'이다. 이를 완료한 후 필요하면 승인 추천 선택 적용을 별도 확장한다.

필수 테스트: context 출처/크기/빈 DB, feature 고정, malformed JSON, invalid response, API key 전송, 202/polling, stage failure, partial correction, wrong feature/ID, repeated review 409, OFF 상태, 기존 CRUD/AI/MCP/RAG 회귀. 공용 수정은 Account/Accommodation도 회귀 확인한다.

## 7. 코드 스타일

사용자의 asd-labs 선호를 유지한다. Flask blueprint + services, 작은 함수, snake_case, 명시적 설정/timeout/예외, 외부 .txt prompt, pytest/requests 패턴을 사용한다. 최신 공용 서버의 SQLite·비동기 API는 호환성을 위해 유지한다. Lab과 현재 main을 무조건 동일하게 만들기 위한 재작성은 하지 않는다.
공용 코드를 변경할 때 현재 압축된 한 줄 함수는 수정 범위 안에서 읽기 쉬운 Lab 스타일로 작성하고, 관련 없는 전면 formatting은 피한다.

참고 CI: https://github.com/Look0n/TripAgent/actions/runs/39175768269
과거 RAG 증거: https://github.com/Look0n/TripAgent/blob/e7fc4120a1141ade47c00ac49c6f4deea9857cec/docs/evidence/agentic-loop/runs/rag-20261004T051412Z-68fffb56.md
Lab 10: https://github.com/Georges034302/asd-labs/blob/main/Lab_10_Multi_Agent_Coordination.md
Lab 11: https://github.com/Georges034302/asd-labs/blob/main/Lab_11_Testing_Deployment_and_Operations.md
