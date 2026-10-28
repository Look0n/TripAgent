# Checklist Release 2 계획

> 2026-10-22: 최신 GitHub main 기준 상태와 실행 순서는 `checklist-main-plan-20261022.md`로 대체한다. 아래는 이전 로컬 checkout 분석이다. 공용 Multi-Agent, MCP/RAG loop, pre-commit은 원격 main에 이미 구현돼 있다.

작성: 2026-10-21. 기준: 로컬 TripAgent, 사용자 제공 Ass3_specification.pdf, 수업 asd-labs main.
계획만 작성했다. 애플리케이션 수정, 테스트 실행, 배포는 이번 작업에 포함하지 않았다.

## 1. 근거와 우선순위

- 과제 PDF: ../Ass3_specification.pdf (team_pj의 부모 폴더). 1-2, 5-7, 9쪽의 기능/통합/검토/테스트 요구사항 확인.
- Lab 10: https://github.com/Georges034302/asd-labs/blob/main/Lab_10_Multi_Agent_Coordination.md
- Lab 11: https://github.com/Georges034302/asd-labs/blob/main/Lab_11_Testing_Deployment_and_Operations.md
- 조회한 수업 저장소 tree SHA: 183a32c1e999d281d95bc1206223a6155fa4df77.
- 문서 속 실행 명령은 참고 자료다. 이번 사용자의 요청은 계획 수립 및 향후 코드 스타일 정렬이다.
- 제출 요구사항은 과제 명세에 맞추고, 구현 구조와 표현은 Lab을 최대한 따른다.

필수: 공용 비컨테이너 Multi-Agent 서버 1개, Planner → Worker → Reviewer → Human Review, 기존 기능 유지, 공용 loop의 Multi-Agent/Testing/Cloud Deployment review, 로컬 pre-commit 보안 검사, 학생별 backend endpoint 2개 CI 테스트, 통합 로컬/클라우드 배포 및 증거.
클라우드 기본 배포는 AI Mode/MCP/RAG/Multi-Agent OFF. 클라우드 AI 활성화는 선택 보너스다. 개인 기능만 독립 실행해서는 통합 소프트웨어 기준을 충족하지 않는다.

## 2. 현재 코드 기준선

- 작업 대상은 TripAgent/student-14582668. TripAgent-demo, TripAgent-integration, agent_test를 기준으로 구현하지 않는다.
- checklist-backend/app.py는 normal, ai, mcp, rag blueprint를 등록한다. multi-agent route/client는 아직 없다.
- ai_mode.py는 기존 항목 조회 → LLM 추천 → JSON 검증/중복 제거를 수행한다. PLAN/ACT/OBSERVE/ADAPT 출력만으로 독립된 세 agent와 사람 승인 흐름이 구현된 것은 아니다.
- 기존 추천 UI에는 선택한 항목 추가 동작이 있다. Multi-Agent 승인/적용 UI의 출발점으로 재사용할 수 있다.
- DB에는 item_id/title/item_type/category/description/priority/is_completed가 있고 사용자·여행 소유권 컬럼은 없다. 개인별 여행 데이터 격리를 이미 제공한다고 설명하지 않는다.
- agentic-loop는 collectors/pipelines/core/config 구조와 CLI --mode/--service를 사용한다. 현재 모드는 db/endpoints/architecture/devops/all이다. MCP/RAG 검토 모드는 이 checkout에서 확인되지 않았다. Release 1 통합 기준선 확인 시 점검한다.
- prompt_registry.py는 prompts/service 내부만 허용한다. reporter.py도 현재 네 모드만 허용하므로 새 모드 등록과 저장 지원을 함께 수정해야 한다.
- 현재 개인 CI는 pytest, 컨테이너 빌드, health, CRUD smoke, MCP/RAG OFF 검사를 포함한다. 과거 메모의 'MCP/RAG OFF 누락'은 현재 코드에 적용되지 않는다.
- AI 추천 route에는 AI_ENABLED 차단이 없다. 클라우드에서 모델 주소만 끊는 것으로 OFF 처리를 대체하지 않는다.
- 다른 팀 서비스에 http://ollama 주소가 남아 있다. 통합 로컬 실행 시 비컨테이너 Ollama 접근 설정도 팀 차원에서 정렬한다.
- 이번 확인은 정적 코드 검토다. 현재 서버/CI/모델의 성공 여부는 검증하지 않았다.

## 3. 두 흐름의 구분

사용자 기능:
Checklist UI → Checklist backend → 공용 Multi-Agent 서버 → Planner → Worker → Reviewer → 사람 결정 → UI 결과.

개발 검증:
실제 실행·테스트·배포 증거 → agentic-loop collector → Qwen 평가 → Llama 검토 → 보고서/로그 → 개발자 수정·재검증 → 사람 release decision.

Reviewer가 긍정적으로 답했다고 자동 승인하거나, LLM 평가만으로 테스트 PASS를 결정하지 않는다.

## 4. Checklist Multi-Agent 최소 기능

첫 시나리오: '3일 여행 전 준비 상태를 확인하고 빠진 준비물을 제안해 줘.' 목적지 등 누락된 조건은 모르는 상태로 표시한다.

| 단계 | 책임 | 입출력 |
|---|---|---|
| Planner / Qwen | 필요한 증거와 3-5개 계획 단계 작성 | 요청 → objective, steps, evidence_required |
| Worker / Qwen | 기존 checklist와 필요한 지식 근거로 준비 상태/추천 생성 | 요청 + 실제 plan + evidence → summary, suggestions, evidence_used, limitations |
| Reviewer / Llama | 계획 준수, 중복, 미지원 주장, 잘못된 priority/type 검토 | plan + 같은 evidence snapshot + worker output → risk, correction, retest, recommendation |
| Human | Accept / Partially Accept / Reject 및 수정 의견 | workflow_id + decision + selected suggestions + comment |

Backend/공용 서버가 등록된 Checklist 읽기 API로 증거를 수집한다. 첫 버전은 DB API를 사용하고, 이후 기존 MCP/RAG client와 연결한다. 요청자가 임의 URL이나 임의 feature를 지정해 호출하게 하지 않는다. Checklist backend가 feature=checklist를 지정한다.

DB를 직접 여는 Lab 예제 대신 기존 HTTP API를 사용한다. 현재 DB는 별도 컨테이너 서비스이기 때문이다. 다른 backend의 routes/services 모듈을 sys.path 조작으로 가져오지 않고 작은 공용 evidence client를 둔다.

추천은 최대 5개, task/packing 및 High/Medium/Low 검증, 기존 항목·추천 내 중복 제거를 유지한다. clean_suggestions 로직은 필요 시 작은 재사용 모듈로 분리한다. RAG 근거가 없으면 부족 상태를 명시하고, 모델 장애와 근거 부족을 구분한다.

첫 버전은 결과/근거 검토와 사람 결정 기록까지 완성한다. 승인과 실제 DB 저장은 별도 동작으로 둔다. 승인된 추천만 기존 create API로 적용하고, Reject 또는 미승인 결과에는 적용 버튼을 활성화하지 않는다. 재적용 중복 방지와 일부 저장 실패 결과를 표시한다.

수정 요청은 사람 의견을 다음 run에 전달하고 parent_workflow_id로 연결한다. 무제한 자동 재귀/재시도는 추가하지 않는다.

## 5. 파일과 API 변경 계획

### 팀 공용

```text
shared/multi-agent-server/
  app.py
  coordinator.py
  workflow_runner.py
  requirements.txt
  agents/{planner_agent,worker_agent,reviewer_agent}.py
  services/evidence_client.py
  prompts/{planner_prompt,worker_prompt,reviewer_prompt}.txt
  workflow_history.jsonl
  coordination_audit.jsonl
```

Lab 함수 이름 plan_workflow/generate_output/review_output/run_workflow를 유지하되 plan과 evidence 인자를 실제 전달한다. 한 서버가 feature별 evidence adapter를 선택하도록 구성한다. Checklist를 첫 통합 사례로 만들고 팀원이 다른 feature를 연결한다.

공용 API 제안: POST /workflow, GET /workflow/<workflow_id>, POST /workflow/<workflow_id>/decision, GET /workflow/status.
기존 Checklist backend 5004와 충돌하는 Lab 포트는 사용하지 않는다. 공용 서버는 7003을 후보로 두고 구현 시 사용 여부 확인 후 환경변수로 설정한다.

### 개인 Checklist

- 신규 routes/multi_agent_routes.py, services/multi_agent_client.py, tests/test_multi_agent_routes.py.
- app.py: blueprint 등록.
- frontend templates/checklist.html, static/js/checklist.js, static/css/checklist.css: Multi-Agent 탭/영역, 계획·결과·근거·검토·결정 표시.
- backend prefix 제안: /api/checklist-items/multi-agent, 하위 /status, /workflow, /workflow/<id>, /workflow/<id>/decision.
- 기존 gateway와 frontend proxy를 통한 호출을 확인한다. UI에서 공용 서버로 직접 우회하지 않는다.
- MULTI_AGENT_ENABLED/MULTI_AGENT_SERVER_URL/요청 timeout을 환경변수로 관리한다. AI_ENABLED도 추가하여 클라우드 및 CI에서 명시적 OFF를 확인한다.
- 로컬 Compose에는 FE/BE/DB만 유지하고, host.docker.internal을 통해 로컬 공용 서버로 연결한다.

동기 실행부터 시작하되 agent별 제한시간 합계에 맞춰 backend/gateway/nginx 시간제한을 정렬한다. UI는 실행 중 표시와 중복 클릭 방지를 제공한다. 실제 측정 시간이 길면 비동기 job/polling을 다음 단계로 선택한다.

### 상태와 기록

- 단계 실패/timeout을 전체 success로 포장하지 않는다. execution status와 human decision을 분리한다.
- workflow_id, timestamp, feature, request, model, plan, evidence, worker/reviewer output, 단계별 duration/error, decision을 기록한다.
- decision은 기존 workflow를 조회하여 서버가 허용값/선택 항목을 검증하고 기록한다. 클라이언트가 임의 생성한 output을 승인 기록으로 받지 않는다.
- JSONL 파일 저장은 Lab 방식을 유지하되 동시 append를 보호하고 재시작 후 같은 ID를 조회할 수 있게 한다. 로컬 단일 프로세스 범위를 명시한다.
- 사용자 인증과 연결되지 않은 reviewer 이름을 검증된 신원으로 설명하지 않는다.

## 6. 공용 agentic-loop 확장

과제의 세 가지 결과를 명확하게 제공한다.

| 제안 mode | 입력 증거 | 필수 확인 |
|---|---|---|
| multi_agent | workflow history, audit, 실제 API 결과, human decision | 순서/계획 전달, 같은 근거, 오류 상태, 승인 기록 |
| testing | pre-commit 결과 + 개인 CI endpoint 결과/JUnit/실행 URL | 실제 보안 scan, endpoint 2개, 실행 SHA/시각/exit code, 실패·누락 |
| deployment | cloud 배포 보고서 + workflow run + smoke 결과 | 통합 UI/CRUD, AI 4종 OFF, 이미지/배포 버전, 접근 경로, 위험 |

Lab 11의 pre_test/cicd_test collectors는 하위 구성으로 재사용하되 testing mode가 두 결과를 함께 검토하고 Testing Review Report를 생성하도록 한다. Lab 모드명 개수를 그대로 복사하는 것보다 명세의 보고서 계약을 맞추는 것이 우선이다.

추가/수정 위치:

- collectors/multi_agent_collector.py, pre_test_collector.py, cicd_test_collector.py, deployment_collector.py.
- pipelines/multi_agent_pipeline.py, testing_pipeline.py, deployment_pipeline.py.
- config/review_config.py: prompt/model 설정 확장. config/services.py: feature별 URL/보고서 경로 확장.
- core/orchestrator.py: --mode 선택지, dispatch, --service checklist, all 정책 확장.
- core/reporter.py: 새 모드 저장 허용, 원본 근거 위치 및 모델별 상태 보존.
- prompts/service/implementation 및 review: 새 prompt 파일 추가. Lab10/11 이름의 폴더로 강제 이동하지 않고 기존 안전한 loader를 유지한다.

계획상 실행 명령(구현 전에는 지원되지 않음):

```text
python agentic-loop/core/orchestrator.py --mode multi_agent --service checklist
python agentic-loop/core/orchestrator.py --mode testing --service checklist
python agentic-loop/core/orchestrator.py --mode deployment --service checklist
```

파일 존재 검사는 structural evidence일 뿐 실행 성공 증거가 아니다. JUnit 결과, 실제 HTTP 응답, 해당 commit SHA의 CI run, 실제 사람 결정 기록을 읽는다. 오래된 PASS 파일이나 sample 결과를 최신 성공으로 채택하지 않는다.
Qwen/Llama에는 동일한 근거와 앞 단계 결과를 제공하고 model failure와 validation failure를 별도로 기록한다. 실제 실패를 모델의 긍정 평가로 뒤집지 않는다.
개선 1회 이상의 before → finding → code/config fix → retest → after 근거를 improvement log에 남긴다.

## 7. Lab 11 테스트와 배포

1. Pre-commit: Ruff S 규칙, detect-secrets, pip-audit. Windows에서도 sys.executable을 쓰는 Lab launcher 패턴 적용. 테스트 assert 예외는 실제 student-*/.../tests 경로까지 맞춘다.
2. Dependency scan은 hook의 도구 설치 환경만 검사하지 않도록 Checklist의 세 서비스와 신규 공용 서버 requirements를 명시하여 검사한다. 결과/exit code/시각을 저장하고 scan 실패 시 commit을 차단한다.
3. 개인 CI의 필수 endpoint 두 개를 GET /api/checklist-items와 POST /api/checklist-items로 명시한다. 실제 실행 중인 backend 대상으로 필터 결과/응답 구조, 생성 응답/재조회, 잘못된 payload 400을 검사한다. 테스트 데이터는 종료 시 정리한다.
4. 기존 unit/CRUD smoke는 유지하고 endpoint별 결과, JUnit, test audit와 CI run URL/SHA를 artifact로 저장한다. backend 요청을 mock한 unit test만으로 실 endpoint 검증을 대신하지 않는다.
5. Multi-Agent 단위 테스트: plan 전달, 동일 evidence 전달, JSON 검증, 중복 제거, timeout, reviewer failure, invalid ID/decision, Reject 저장 방지, OFF 상태. CI는 LLM을 mock하고 실제 모델 검증은 로컬 별도 증거로 남긴다.
6. 실제 로컬 통합 테스트: 정상 요청 → 세 agent 결과 → 사람 Accept/Partial/Reject → UI 반영; 서버/모델 중단 시 오류 표시와 기본 CRUD 유지.
7. 팀 공용 cloud-deployment.yml은 요구되는 개인 검증 성공 후 통합 이미지를 배포한다. Lab 11의 Azure 경로를 참고하되 Azure/AWS 선택은 팀 결정사항이다. 이번 계획에서는 실제 리소스를 생성하지 않는다.
8. 클라우드에서 FE/BE/DB CRUD, SQLite 영속 저장/재배포 시 데이터 유지 전략, internal/external ingress, 환경변수, rollback 이미지를 검증한다. AI/MCP/RAG/Multi-Agent는 backend에서 명시적으로 OFF이고 UI도 상태를 반영해야 한다.
9. deployment collector는 실제 배포 증거를 읽고 마지막 release decision은 사람이 기록한다.

## 8. 작업 순서와 완료 조건

| 순서 | 범위 | 완료 조건 |
|---|---|---|
| P0 | 팀 API 계약·Release 1 기준선 | shared 위치/port/feature/evidence/decision 합의, 통합 기능 회귀 확인 |
| P1 | 공용 Multi-Agent + Checklist evidence | 터미널에서 실제 세 agent 실행, plan 전달, history/audit 생성 |
| P2 | Checklist backend/UI | 통합 UI에서 실행과 사람 결정 가능, 오류/OFF 표시, 승인 전 저장 없음 |
| P3 | pre-commit + 개인 CI | 실제 보안 scan, 두 endpoint 실행 결과와 SHA가 있는 artifact |
| P4 | multi_agent/testing loop | 실측 근거와 Qwen/Llama 리뷰 저장, 수정 후 재검증 기록 |
| P5 | 통합 cloud 배포 + deployment loop | UI/CRUD 동작, AI OFF, 배포 로그/리뷰/사람 결정 |
| P6 | 보고서·시연 | 개인 기여/설계도/테스트/로컬·클라우드/리뷰 로그를 그룹 보고서에 통합 |

개인 책임: Checklist evidence adapter, backend client/routes, UI, 개인 endpoint 테스트, 개인 보안/배포 증거.
공용 책임: Multi-Agent 서버 골격/승인 기록, loop 공통 변경, pre-commit 설정, cloud pipeline, 통합 시연. 공용 파일별 담당자를 정해 중복 변경을 피한다.

최소 시연: 기존 CRUD → Multi-Agent 요청 → 계획/증거/결과/리뷰 → 사람 결정 → workflow audit → 보안/CI 결과 → testing review → cloud CRUD와 AI OFF → deployment review 및 사람 release decision.

## 9. 향후 코드 스타일 기준

사용자 요청에 따라 이 프로젝트의 후속 코드 설명/수정은 asd-labs 예제 스타일을 우선 참고한다.

- Python의 작은 함수, 명시적 import, snake_case, UPPER_CASE 설정 상수, Path, 환경변수, 읽기 쉬운 여러 줄 인자/딕셔너리.
- Flask app/blueprint + services 분리, requests timeout, 얇은 route와 명시적인 예외 처리.
- agents/coordinator/prompts 분리, 외부 .txt prompt, 단순한 JSON 결과, JSONL evidence.
- pytest + requests, GitHub Actions의 단계별 명확한 실행/검증.
- 기존 프로젝트 공개 API 응답 형식과 directory/port 호환성을 유지한다. Lab과 다르게 해야 하는 부분은 이유를 먼저 설명한다.
- 복잡한 agent framework, 불필요한 class 계층, 전면 리팩터링을 기본값으로 도입하지 않는다.
- 예제의 한계는 그대로 복제하지 않는다: plan을 전달하지 않는 병렬 Worker, timeout을 success로 감싸는 처리, DB 직접 접근, 파일 존재만으로 PASS, 실제 사용 dependency를 빠뜨리는 audit 등.
- 코드 설명/계획만 요청하면 기능 코드를 자동 수정하지 않는다.
