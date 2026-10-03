# Trip Checklist Release 1 분석 및 구현 계획

작성: 2026-10-01, 대상: `student-14582668`, 기준 커밋: `4518106c1b377d28ccd39067bca62ee0ea168ba9`.

## 작업 범위와 현재 상태

### 최신 진행 점검 (사용자 MCP 코드 입력 후, 2026-10-01)

사용자가 client/tools/server 코드를 입력했다. 아래는 최초 점검에서 발견했던 항목이며, 사용자 수정 후 재확인에서 5개 모두 해결된 것을 확인했다. Checklist registry 네 항목과 MCP wrapper 3개도 존재한다. 기능 코드를 대신 수정하거나 런타임 성공을 확인한 것은 아니다.

1. `shared/mcp-server/services/checklist_client.py`: `method=methid`를 `method=method`로 수정.
2. 같은 파일의 목록 함수 `get_checklist_items`를 `get_items`로 변경해 tools의 import와 일치시킴. 공개 MCP 이름은 get_checklist_items 유지.
3. `shared/mcp-server/tools/checklist_tools.py`: `catetory = category.strip()`를 `category = category.strip()`로 수정.
4. 같은 파일의 `item.get("priority)")`를 `item.get("priority")`로 수정. 현재 키로는 High 미완료 집계가 0이 됨.
5. `shared/mcp-server/tool_registry.py`: CHECKLIST_TOOLS 및 FEATURE_TOOL_ACCESS, TOOL_CATEGORY, get_registry_summary에 checklist 등록. 서버는 이미 CHECKLIST_TOOLS를 import 중이라 누락 시 시작 불가.

현재 다음 실행 순서(위 오류 수정은 완료):

- 수정 후 import 확인, 실제 MCP initialize/list_tools/call_tool로 3개 도구 성공·입력 오류·없는 ID·backend 장애 검증.
- `student-14582668/checklist-backend/services/mcp_client.py` 신규: Account SDK 패턴, 결과 정규화, isError와 success=false 처리, OFF 차단.
- `routes/mcp_routes.py` 신규: `/api/checklist-items/mcp/status`, `/tools`, `/call`; checklist 전용 허용 도구와 요청 검증.
- backend app.py blueprint 등록, requirements에 공용 서버와 호환되는 MCP SDK 추가, Compose에 MCP URL/OFF 설정 및 host 접근 구성.
- 기존 checklist.html/js/css에 MCP 목록/단건/요약 UI 연결. 통합 gateway 경로를 사용하고 backend OFF를 UI에서 해제할 수 없게 함.
- MCP UI 성공 및 장애/기존 CRUD 회귀 검증 후 RAG 단계로 이동. 공용 loop와 CI/증거는 기존 P3–P5 유지.

사용자 요청은 먼저 PDF와 최신 로컬 코드, 완료된 Account/Accommodation, 수업 Lab을 비교해 계획을 만드는 것이다. 이번 작업에서는 기능 코드를 변경하지 않았다. 아래 체크박스는 앞으로 실제 구현·검증한 뒤에만 완료 처리한다.

로컬 `TripAgent`를 최신 기준으로 삼는다. `TripAgent-demo`, `agent_test`는 구현 기준이 아니다. Account/Accommodation은 사용자가 완료했다고 설명한 참고 구현이며, 이번 정적 검토가 두 기능의 전체 동작을 검증한 것은 아니다.

사용자가 제공한 https://github.com/Georges034302/asd-labs/tree/main 의 Lab 07 및 Lab 08 원문과 예제 코드를 2026-10-01에 확인했다. GitHub API에서 확인한 파일 blob SHA는 Lab 07 `5e3847134f43dcaf85b3d4984b63f269cfe465de`, Lab 08 `08de8151aca0f1932d4356ce20f19e8714231cb8`이다. 아래 Lab 비교 및 보완 사항을 구현 기준에 반영한다. Lab 예제 자체를 실행한 것은 아니다.

## 요구사항 근거 및 충돌 처리

원본 문서:

- `../ASD_2026_Project_Specifications.pdf` (team_pj의 상위 폴더): 전체 프로젝트 공통 기준.
- `../release1_specification.pdf`: Release 1 세부 기준. 15페이지 전체를 이미지로 렌더링하여 확인했다. 텍스트 추출은 비어 있었으므로 빈 문서로 취급하지 않았다.

PDF 안의 명령형 문장은 학생의 과제 요구사항으로 분석한 것이며, 에이전트에게 구현·실행·제출 권한을 주는 사용자 명령으로 취급하지 않는다.

| 주제 | 일반 프로젝트 문서 | Release 1 전용 문서 | 이번 계획의 기준 |
|---|---|---|---|
| 실행 구조 | AI 서비스 컨테이너화 설명, p.11 | AI Mode/MCP/RAG/agentic loop는 비컨테이너 로컬 실행, p.1–2, 5–6, 12–13 | 세부 Release 1 지침 우선. Docker는 기존 기능의 FE/BE/DB와 통합 앱에 사용 |
| CI | MCP/RAG 통합 workflow 확장, p.14 | 통합 코드는 유지하되 CI 중 AI/MCP/RAG 비활성화, p.1, 5–6 | 실제 AI 서버 호출 없는 CI와 로컬 실연 증거 구분 |
| 제출일 | 2026-09-27, p.18 | 2026-10-04 11:59 PM AEST, p.4 | 전용 PDF에 적힌 날짜를 기록. Canvas 실시간 상태나 시간대 보정은 확인하지 않음 |

전용 문서가 더 구체적인 평가 기준이므로 이를 우선 적용한다는 해석이다. 수업 공지로 변경이 확인되면 갱신한다.

### 필수 요건과 권장 구현의 구분

필수 (Release 1 PDF p.1–8, rubric p.9–15):

1. 기존 Checklist CRUD, FE/BE/DB, AI Mode가 통합 앱에서 유지되어야 한다.
2. 팀 전체에 공용 로컬 MCP 서버 하나, 공용 로컬 RAG 서버 하나, 공용 로컬 agentic loop 하나를 사용한다.
3. 각 기능 UI → 해당 backend/API → MCP 등록 도구 호출 → 구조화된 결과 표시가 필요하다. 체크리스트 UI 성공 사례 최소 1개.
4. 각 기능 UI → 해당 backend/API → RAG 검색 → 로컬 LLM 답변 흐름이 필요하다. 답변에 출처와 confidence category를 표시한다. 체크리스트 UI 성공 사례 최소 1개.
5. 관련 근거가 없으면 unsupported answer 대신 insufficient-context를 표시하고 이를 검증한다.
6. MCP 도구의 입력·출력·접근 범위를 정의하고 적용한다.
7. 공용 agentic loop에 기존 모드와 별도로 MCP/RAG validation 모드를 추가하고 두 모드의 실행 결과를 보관한다.
8. 개인 CI workflow를 업데이트하고 실제 성공 run 링크 또는 실행 로그를 남긴다. CI에서는 AI/MCP/RAG를 끈다.
9. Compose 실행, 로컬 터미널 MCP/RAG 검증, UI 상호작용, grounded answer, 통합 검증 증거를 남긴다.
10. 개인 기여 로그, 확인 가능한 Release 1 커밋, 아키텍처·상호작용 도식, 알려진 제한사항을 팀 보고서에 제공한다.

일반 문서에서 유지할 사항: 각 DB 테이블 최소 10 records (p.2–3), 통합 홈페이지/공통 테마, 승인된 Ollama/Llama/Qwen/DeepSeek, Plan → Act → Observe → Adapt, Git branches/PR/commit history.

문서에는 체크리스트 전용 MCP 도구를 정확히 5개 만들라는 규정, 모든 CRUD를 MCP로 구현하라는 규정, 특정 embedding 모델이나 정량 retrieval 목표가 없다. 아래 도구 수·API 이름·테스트 수는 제안이다. 다중 에이전트 Planner/Worker/Reviewer 및 클라우드 배포는 Release 2 범위다.

## 현 코드 분석

| 부분 | 확인한 상태 | 해야 할 일 |
|---|---|---|
| Checklist 기본 기능 | `checklist-backend/routes/normal_ui.py`에 CRUD/필터, `routes/ai_mode.py`에 추천·중복 제거·최대 5개 제안 | 유지하고 회귀 검증 |
| DB | `checklist_items` 1개 테이블, `init.sql`에 10개 seed | 실행 DB count 확인. 현재 스키마에는 customer_id/trip_id가 없음 |
| AI UI | 추천 표시 및 사용자가 Add to checklist로 저장하는 구조 | 기존 사용자 선택 저장 동작 유지 |
| Checklist MCP | `shared/mcp-server/tools/checklist_tools.py`, `services/checklist_client.py`가 0 bytes | 실제 도구·API client 구현 |
| MCP 등록 | `mcp_server.py`와 `tool_registry.py`에 account/accommodation/shared만 있음 | checklist 등록 및 허용 도구 일치 검증 |
| Checklist MCP/RAG backend | `app.py`는 normal/ai blueprint만 등록 | MCP/RAG routes, clients, 모드 제어 추가 |
| Checklist RAG corpus | `corpus/checklist-corpus.jsonl`은 빈 파일; knowledge 리스트도 비어 있음 | 실제 검색할 프로젝트 지식 구성 |
| RAG 경로 | `rag_pipeline.py:31`이 `student-25992424`로 설정됨 | `student-14582668`로 수정 |
| RAG DB loader | checklist는 실제 조회 대신 contract_pending placeholder 반환 | 체크리스트 자료의 source mapping 구현. placeholder는 답변 근거에서 제외 |
| RAG 품질 | hash embedding; lexical fallback; 근거 부족 판단은 주로 prompt에 의존 | 무관한 질문/빈 corpus를 코드와 평가로 검증 |
| RAG 오류 | Ollama 예외가 문자열로 바뀌어 상위 `status=success` 답변이 될 수 있음 | 서비스 오류와 insufficient-context를 분리 |
| RAG 평가 | `rag_eval.py`는 Account 질문 3개용; metrics 문서는 실제 수치 없음 | Checklist용 평가 질문/실제 결과 추가 |
| UI | 체크리스트 전용 MCP/RAG 화면 없음 | 기존 화면에 MCP/RAG 영역 추가 |
| Gateway | `/api/checklist-items/<path>` 프록시가 있어 신규 하위 경로 사용 가능 | 현재 timeout=10초를 AI 호출에 맞게 조정; nginx의 120초 및 내부 timeout도 정렬 |
| Compose | checklist에 MCP/RAG URL·enabled 설정 없음. Ollama/ollama-init은 컨테이너로 정의됨 | checklist 연결 설정 추가. 팀 공통 로컬 Ollama 전환을 별도 통합 작업으로 수행 |
| CI | CRUD/health/pytest 선언은 있음. MCP/RAG OFF 설정 없음 | OFF 설정·공유 파일 trigger·mock 검증·증거 보존 추가 |
| CI 주소 | frontend에 `http://localhost:5005/api/checklist-items` 지정 | direct backend 검증은 5004; 통합 UI 검증은 3000/gateway 경로 사용 |
| 공용 loop | `orchestrator.py` choices는 db/endpoints/architecture/devops/all | mcp/rag 모드 추가 |

추가 공유 위험: accommodation registry의 `get_accommodations_by_city`, `get_available_accommodations`와 실제 서버 등록명 `get_accommodation_by_city`, `check_accommodation_availability`가 다르다. 참고 코드의 패턴은 활용하되 이름 불일치를 복제하지 않는다. Checklist 완료와 별도로 팀 통합 점검 목록에 기록한다.

RAG embedding의 기술적 제한: 256차원 배열을 만들지만 SHA-256 digest의 32바이트만 같은 첫 32칸에 누적한다. 학습된 semantic embedding으로 설명하면 안 된다. 모델 교체는 필수 요건으로 단정하지 않고, Lab 확인 및 관련성 평가 후 결정한다. 변경 시 기존 collection 차원/색인을 함께 재생성해야 한다.

검증 한계: 정적 코드 분석 결과이다. 기존 테스트 함수 17개를 확인했지만 bundled Python에 pytest가 없어 실행 시작 단계에서 실패했다 (`No module named pytest`). 서버 동작, 현재 CI 성공, 모델 응답, 사용자별 데이터 격리는 검증하지 않았다.

## 참고 구현에서 가져올 것

- Account: MCP SDK `ClientSession`, initialize/list_tools/call_tool, structuredContent 우선 결과 정규화, backend tool allowlist, disabled와 unavailable의 구분.
- Accommodation: MCP/RAG 전용 UI, backend routes → client → shared server 흐름, RAG answer/retrieve/refresh 구조.
- Checklist: 현재 `/api/checklist-items` URL 및 gateway 경로, 기존 추천 검증/수동 저장 UX.
- 공용 RAG: feature별 collection/corpus 분리, source_id/chunk_id/authority_tier, audit 구조.

Account의 프로세스 전역 UI 모드 토글을 그대로 복사하지 않는다. CI의 서버 OFF 설정은 UI에서 다시 켤 수 없게 하고, UI의 선택과 서버 기능 허용 여부를 구분한다. Checklist에는 현재 개인 소유권 컬럼이 없으므로 Account의 customer_id 전달만 복사해서 개인별 보호가 완성됐다고 주장하지 않는다. 이번 기본 범위는 기존 공유 체크리스트 데이터 모델을 유지하고 그 한계를 문서화하는 것이다. 개인별 checklist가 요구되면 별도 migration/ownership 검증 작업으로 추가한다.

## 제안 아키텍처 및 API

```text
Browser: localhost:3000/checklist/
  -> shared frontend nginx (/api/*)
  -> shared gateway (session validation)
  -> checklist backend :5004
       -> CRUD -> checklist database :6004
       -> AI Mode -> host Ollama :11434
       -> MCP client -> host shared MCP :7001/mcp
                         -> checklist tool -> existing backend CRUD/read API
       -> RAG client -> host shared RAG HTTP :7002
                         -> checklist corpus / Chroma -> host Ollama

Host shared agentic-loop -> MCP validation / RAG validation -> saved evidence
```

MCP가 backend에 재접근할 때 MCP route를 재호출하지 않고 기존 읽기/CRUD API를 호출해 순환을 피한다. 접근 경계는 backend allowlist만으로 전체 인증이 끝났다고 설명하지 않는다. 공용 MCP의 입력 검증·등록 범위, 로컬 접근 경계, 데이터 API 신뢰 경계도 문서와 테스트에 포함한다.

### MCP 최소 구현 제안

먼저 읽기 전용 도구 3개를 구현한다. 이것만으로 과제의 성공적인 MCP 상호작용을 만들 수 있다.

| 제안 도구 | 입력 | 출력 / 용도 |
|---|---|---|
| `get_checklist_items` | item_type/category/priority/is_completed 선택 필터 | 실제 items와 count |
| `get_checklist_item` | 양의 item_id | 단일 항목 또는 명확한 not_found |
| `get_checklist_summary` | 선택 필터 | total/completed/pending/high_priority_pending 등 실제 집계 |

필요한 경우 `create_checklist_item`, `update_checklist_item`를 추가하되 명시적 사용자 동작으로 저장한다. 자동 삭제나 LLM의 임의 쓰기는 최소 범위에 포함하지 않는다. 5개 도구를 갖추기 위해 불필요하게 범위를 늘리지 않는다.

제안 backend routes:

- `GET /api/checklist-items/mcp/status`
- `GET /api/checklist-items/mcp/tools`
- `POST /api/checklist-items/mcp/call` (`tool`, `arguments`)
- `GET /api/checklist-items/rag/status`
- `POST /api/checklist-items/rag/ask` (`question`; feature는 서버에서 checklist 고정)
- `POST /api/checklist-items/rag/retrieve` (검증용)
- `POST /api/checklist-items/rag/refresh` (검증/관리용, 접근 범위 명시)

동적 도구 이름이나 임의 URL/SQL을 실행하지 않는다. 허용 도구·필드·타입·범위를 검증하고 다른 기능 호출을 거절한다. 정확한 HTTP 오류 계약은 구현 시작 시 고정하고 테스트한다.

### RAG 최소 구현 제안

1. Checklist 프로젝트 지식을 source-controlled 문서로 구성: task/packing 차이, priority, 완료 처리, CRUD, 추천 저장 여부, 체크리스트 준비 항목 설명. 현재 DB 스냅샷을 검색할 경우 indexed_at 및 refresh 필요성을 표시한다.
2. 실시간 상태는 MCP에서 읽고, 사용법/준비 지식은 RAG로 답한다. 일반적인 여행 추천 기능 확장은 선택 사항이다. 비자 규정처럼 corpus에 없는 외부 사실을 만들어 답하지 않는다.
3. `FEATURE_DIRS['checklist']` 수정 및 checklist loader 추가. 문서 내용 자체를 chunk화하고 파일 목록만을 여행 지식으로 사용하지 않는다.
4. 질문 → 검색 → 관련성 확인 → 근거 있는 경우 Ollama 답변. 관련성 없거나 빈 corpus면 명시적 insufficient-context. 이 경우 유효 근거인 것처럼 placeholder citation을 붙이지 않는다.
5. 답변과 실제 사용 chunk의 source_id/chunk_id를 함께 표시. Confidence는 평가된 근거 기반 범주이며 정확도 확률이 아니라고 설명한다. 현재 tier 개수만으로 생기는 과신을 보완한다.
6. UI에는 질문, 답변, 출처, confidence, loading/error/disabled 상태. 검색 디버그 정보는 펼침 영역에 둔다.
7. Checklist 평가 세트 제안: 정상 질문 5개, 근거 없는 질문 2개, 빈/실패 상황 2개 이상. 수치는 구현 계획상의 표본 수이며 과제 명시 숫자가 아니다.

## 구현 순서 및 완료 기준

### P0. 기준선과 공용 실행 구조

- [x] 사용자 제공 Lab URL의 MCP/RAG 원본 및 실행 지침 비교 완료(아래 비교표). 예제 실행 검증은 하지 않음.
- [ ] 프로젝트 Python 환경으로 기존 17개 테스트 실행; 통합 UI CRUD/AI 성공 증거 확보.
- [ ] 로컬 Ollama 모델/포트 확인 후 팀 Compose의 Ollama 의존성 전환 계획 적용. 모든 기능의 URL 형식 차이(base URL, /api/generate, /v1)를 보존.
- [ ] Docker 서비스는 FE/BE/DB 등 통합 앱만 유지. shared MCP/RAG/loop는 로컬 프로세스. MCP/RAG는 컨테이너에 추가하지 않음.
- [ ] checklist env: MCP_SERVER_URL, RAG_SERVICE_URL, MCP_ENABLED, RAG_ENABLED, AI_ENABLED(제안 이름), host 접근 설정 추가.
- [ ] gateway/nginx/backend 요청 timeout을 일관되게 설정. 장애 시 무한 대기 방지.

### P1. MCP 연결

- [ ] shared checklist client/tools 구현 및 실제 FastMCP 등록.
- [ ] tool_registry와 contracts 업데이트, 실제 list_tools와 이름 일치 검증.
- [ ] Checklist backend MCP routes/client 및 허용 범위 구현.
- [ ] 기존 UI에 MCP 결과 영역 연결.
- [ ] 통합 홈페이지에서 미완료 항목 조회 또는 준비 상태 요약 성공. 터미널 요청/응답도 저장.

### P2. RAG 연결과 grounded response

- [ ] checklist 지식 문서, source mapping, 잘못된 학번 경로 수정.
- [ ] corpus refresh → retrieval → Ollama answer 실동작 확인.
- [ ] Checklist backend RAG routes/client 및 UI 구현.
- [ ] 출처·confidence 표시, 무관 질문 insufficient-context 검증.
- [ ] Ollama 장애/검색 장애/빈 corpus/lexical fallback을 성공 답변과 구분.
- [ ] 현재 Account/Accommodation 동작을 회귀 점검. 공유 동작 변경은 필요한 범위로 한정.

### P3. 공용 agentic loop

- [ ] 기존 `--mode`에 `mcp`, `rag` 추가; 기존 모드 유지.
- [ ] MCP collector/pipeline: 발견된 도구, 정상 호출, 잘못된 입력·금지 도구 검증.
- [ ] RAG collector/pipeline: refresh/retrieval/answer/citation/confidence/insufficient-context 검증.
- [ ] Plan → Act → Observe → Adapt 기록 및 실제 응답 근거를 report로 저장.
- [ ] checklist부터 실행하고 팀원 기능까지 같은 validation 방식으로 통합.
- [ ] AI의 검토 문장만으로 PASS를 선언하지 않고 결정적 검증 결과와 실행 실패를 구분.

### P4. CI 및 회귀 검증

- [ ] 개인 workflow에 AI/MCP/RAG OFF 환경값 및 서버 강제 차단 적용.
- [ ] OFF 상태에서 CRUD/health 정상, AI/MCP/RAG 외부 요청 0회 검증.
- [ ] 실제 서버 없이 mock contract/error tests 실행. 실제 MCP/RAG 성공 증거는 로컬 실행에서 확보.
- [ ] 잘못된 CI frontend 포트 수정; UI 호출 경로 검증을 단순 HTML 제목 확인과 구분.
- [ ] checklist 관련 shared 변경도 workflow trigger에 포함.
- [ ] 결과/log artifact와 최신 실행 커밋 SHA, run URL 확보.
- [ ] 기존 workflow명을 임의 변경하지 않고 보고서에서 담당 학생/서비스와 매핑. 수업에서 정확한 파일명 요구가 따로 있으면 확인 후 조정.

### P5. 제출용 증거와 통합 실연

- [ ] 기존 CRUD/AI, MCP 성공, RAG 성공, 근거 부족 사례 UI 증거.
- [ ] MCP 도구 입력/출력/접근 경계 문서 및 터미널 transcript.
- [ ] RAG 원문 chunk → retrieval → answer/citation/confidence 연결 증거.
- [ ] 공용 loop MCP/RAG 모드 각각 실행 결과.
- [ ] Compose config/컨테이너 상태/통합 홈페이지에서 정상 접근 증거.
- [ ] 구현 커밋과 개인 기여 로그, risk/NFR/known limitations 기록.
- [ ] 팀 전체 5개 기능의 통합 체크 및 Account/Accommodation 회귀 확인.

권장 증거 경로: `docs/evidence/release1/checklist/`. 아직 생성되지 않은 실행 결과를 작성하거나 성공으로 표시하지 않는다.

## 최소 데모 시나리오

1. 통합 홈페이지에서 Checklist 진입. 기존 항목 CRUD 및 AI 추천 확인.
2. MCP 영역에서 high priority 미완료 항목/summary 요청. 실제 DB 상태와 일치하는 구조화된 결과 표시.
3. RAG에 “task와 packing의 차이는 무엇인가?” 질문. 저장된 지식을 근거로 답변, source, confidence 표시.
4. corpus에 없는 질문으로 insufficient-context 표시.
5. 터미널에서 공용 loop의 MCP/RAG validation 출력을 보여준다.

팀 보고서: 최대 3000 words + diagrams, 그룹 PDF 1개, 파일명 `group-<group number>.pdf`, 공유 저장소 링크·10분 이하 영상 URL·개인 기여/커밋 증거. 개인별 UI MCP/RAG 성공과 로컬 terminal/loop 실행을 영상에 포함. Week 9 참석/Q&A 요건도 별개로 충족해야 한다.

## 다음 작업을 위한 기억

- 지금은 계획 단계. 사용자가 구현을 요청하면 P0부터 순서대로 진행하고 상태를 갱신한다.
- 가장 큰 필수 누락은 Checklist MCP/RAG 전체 연결, RAG 실제 지식, 공용 loop 2개 validation 모드, CI OFF, 로컬 AI 실행 구조 정렬이다.
- Lab 07/08 원본 비교 완료. 아래 보완 항목까지 포함해 구현한다. Lab의 샘플 결과를 실제 실행 결과로 사용하지 않는다.
- 기능 1개의 완료와 팀 Release 1 전체 완료를 구분한다.
- 저장한 메모는 이 문서와 `team_pj/MEMORY.md`이다. 자동 전역 장기 메모리 등록을 뜻하지 않는다.

## 2026-10-01 Lab 07/08 비교 후 확정한 보완 사항

직접 확인한 원본:

- [Lab 07 MCP and Enterprise Integrations](https://github.com/Georges034302/asd-labs/blob/main/Lab_07_MCP_and_Enterprise_Integrations.md): §4 서버/프런트/백엔드 코드, §5 검증, §6–8 loop 및 증거.
- [Lab 08 RAG and Enterprise Context Pipelines](https://github.com/Georges034302/asd-labs/blob/main/Lab_08_RAG_and_Enterprise_Context_Pipelines.md): §1 실행 구조, §4 pipeline/evaluation/HTTP/UI 코드, §5–8 검증·loop·증거.

Lab은 Student Enrolment 교육 예제다. 예제의 student_count 등 도구 이름·개수, 학생 DB 경로, 5003 포트, 메뉴 번호를 TripAgent 과제의 필수 고정값으로 해석하지 않는다. Release 1 PDF를 평가 기준으로, Lab을 구현·검증 패턴의 참고 자료로 사용한다.

| Lab에서 확인한 내용 | TripAgent 적용 결정 |
|---|---|
| Lab 7은 count/filter/files/CI 네 가지 도구 예제 | Checklist 조회/단건/요약 3개를 최소 범위로 유지. 파일/CI 도구를 개수 맞추기 위해 추가하지 않음 |
| Lab 7 실제 Flask MCP route는 DB API 또는 파일을 직접 읽음. 터미널/collector도 Python 함수를 직접 호출 | 이것만으로 MCP 프로토콜 연결 검증이 되지는 않음. Account의 실제 ClientSession → Streamable HTTP MCP 호출 유지. 실제 initialize/list_tools/call_tool 결과 확보 |
| Lab 7 SDK 설명은 MCPServer/2.x지만 코드 import는 FastMCP이고 1.x 호환도 언급 | 현재 프로젝트 `mcp>=1.28,<2`와 FastMCP를 유지. 문구만 보고 major upgrade하지 않음. 설치 버전·연결 호환성을 실제 검증 |
| Lab 8은 비컨테이너 RAG/Ollama, 컨테이너 backend에서 host.docker.internal 연결 | 기존 실행 구조 계획을 재확인. TripAgent 포트 MCP 7001/RAG 7002 유지. Lab 5003은 TripAgent attractions 포트와 충돌 |
| Lab 8은 refresh_corpus/retrieve_context/answer_question 3개 공용 연산 | 이미 존재하는 shared pipeline/HTTP API를 재사용. Checklist용 서버를 별도로 만들지 않음 |
| Lab 8 corpus는 DB 사실, 보고서, 저장소 목록의 3개 tier | Checklist API의 실제 DB snapshot + 기능 지식 문서로 유용한 corpus 구성. report/repository는 해당 질문의 관련성 있을 때만 근거로 사용 |
| Lab 8 hash embedding·80-word chunking·Chroma·lexical fallback | 현재 shared 구현이 이 패턴을 따른다는 점 확인. 학습 embedding 교체는 필수 아님. 한계와 retrieval_mode를 기록하고 실제 관련성 평가로 판단 |
| Lab 8 rag_eval.py는 3개 benchmark의 P@5/R@5를 계산하고 metrics 파일에 기록 | 기존 TripAgent 평가 스크립트는 단순 Account 출력이므로 Checklist 평가 및 실제 metrics 파일 기록을 계획에 추가 |
| Lab 8 audit는 input/output, request_id/trace_id, timestamp, duration, validation/outcome 기록 | 기존 audit 활용. UI 요청→검색→답변을 같은 trace로 연결하는 보완을 권장(현재는 연산별 UUID 생성) |
| Lab 7/8 loop는 evidence → Qwen 구현 평가 → Llama 검토 | 프로젝트 기존 두 모델 검토 패턴에 MCP/RAG 모드를 추가. RAG quality 및 reasoning 두 review prompt를 실제 호출에 연결 |
| Lab 8 collector는 파일 존재/함수 정의 검사에 그침 | 정적 검사는 정적으로 표기. 실시간 검색/답변/citation/insufficient-context는 별도 실행 검증으로 확보 |
| Lab 8 loop 예제는 console 출력만 하고 보고서를 자동 저장하지 않음 | TripAgent 기존 reporter를 확장해 실제 결과 저장. 빈 파일이나 샘플 PASS를 증거로 쓰지 않음 |

### P1 추가: 실제 MCP 경로를 입증

- [ ] 서버를 켠 상태에서 UI → backend → shared MCP → 기존 데이터 API 결과 확인.
- [ ] MCP 서버가 꺼지면 MCP UI 요청이 명확한 unavailable로 실패하고 기본 CRUD는 작동하는지 확인. MCP를 우회한 직접 DB 응답을 성공으로 표시하지 않음.
- [ ] tool contract에 purpose/input/output/failure/read-only boundary를 포함.
- [ ] UI ON/OFF를 제공하는 경우 backend의 서버 OFF 설정이 항상 우선. X-MCP-Mode/X-RAG-Mode를 사용할 경우 gateway가 현재 전달하지 않는다는 점을 반영해 허용 헤더 전달을 구현·검증하거나 다른 명시적 방식으로 설계.

### P2 추가: 평가 가능한 RAG 구현

- [ ] Checklist 평가 질문마다 관련 정답 chunk ID 집합을 정의하고 corpus 버전/refresh 시각 기록.
- [ ] P@5 = top-5 안의 관련 chunk 수 / 5. R@5 = top-5 안의 관련 chunk 수 / 해당 질문의 전체 관련 chunk 수. 정답 근거가 없는 질문은 recall N/A로 구분하고 insufficient-context 정확성을 별도 검증.
- [ ] Lab 예제의 keyword-any 매칭, 수동 expected_relevant 값, recall을 1로 자르는 방식은 간단한 실습용 평가다. 프로젝트에서는 명시적 chunk ID relevance labels를 사용해 과대평가를 피한다.
- [ ] `rag_eval.py`에 checklist 선택 기능을 추가하거나 별도 checklist evaluator를 작성. Account 평가 동작 보존. metrics는 feature별 증거 폴더에 저장해 서로 덮어쓰지 않음.
- [ ] 최소 3개의 답변 가능한 benchmark를 포함하고 기존 계획의 정상/무관/장애 사례까지 확장. 과제 PDF에는 특정 P@5/R@5 합격 숫자가 없으므로 임의 목표를 공식 기준으로 쓰지 않음.
- [ ] 정상 grounded answer 사례는 실제 로컬 Ollama 응답으로 확보. Lab의 deterministic_answer 같은 정형 결과만으로 LLM 흐름 검증을 대신하지 않음.
- [ ] DB snapshot을 색인하면 CRUD 후 refresh로 결과가 갱신되는지 검증. 최신 상태 질문은 MCP와 구분.

Lab 코드에도 관련성이 없는 chunk가 반환될 수 있고 confidence는 tier 개수 위주이며 Ollama 예외가 성공 답변 문자열로 포장될 수 있다. 따라서 앞서 계획한 관련성 판별·근거 부족·오류 구분 개선을 유지한다. 이는 Lab 예제를 무조건 그대로 복사하면 해소되지 않는다.

### P3 추가: prompt와 reporter 연결

현재 `agentic-loop/core/prompt_registry.py`는 `prompts/service` 내부만 읽는다. Lab의 `prompts/lab7`, `prompts/lab8` 경로를 그대로 추가하면 현재 loader와 맞지 않는다.

- [ ] 최소 변경안: `prompts/service/implementation/mcp_task_prompt.txt`, `rag_task_prompt.txt` 및 `review/mcp_integration_review_prompt.txt`, `mcp_tool_review_prompt.txt`, `rag_review_prompt.txt`, `rag_reasoning_prompt.txt`로 프로젝트 naming에 맞춰 추가.
- [ ] review_config에 MCP/RAG prompt 매핑을 추가하고, 필요 없는 prompt 파일을 만들어 방치하지 않음. RAG quality/reasoning 검토를 모두 실행에 반영.
- [ ] 실제 MCP 도구 응답과 RAG 검색/답변 evidence를 먼저 수집. 모델은 그 evidence를 평가하며 정적 검사만으로 런타임 성공을 추론하지 않음.
- [ ] 이 두 모델 검토는 기존 공유 개발 검증 loop 확장이다. Release 2 제품용 Planner/Worker/Reviewer 다중 에이전트 서버를 새로 구현하는 작업과 구분.

### P5 추가: Lab 증거를 프로젝트 경로로 매핑

권장 위치 `docs/evidence/release1/checklist/` 아래:

| 파일 | 내용 |
|---|---|
| `run-report.md` | MCP 실제 터미널/UI 요청·응답, 실행 시각·버전 |
| `boundary-analysis.md` | Checklist 도구 범위·허용 입력·접근 경계 |
| `tool-review.md` | 실제 발견된 문제와 수정/재검증. 미수정 항목은 미수정으로 표시 |
| `integration-report.md` | UI/backend/shared MCP 연결 및 회귀 결과 |
| `rag-report.md` | refresh/retrieve/answer 및 근거 부족 실측 |
| `retrieval-metrics.md` | 질문·정답 chunk·검색 chunk·P@5/R@5·검색 모드 |
| `rag-validation-report.md` | 공용 loop 실제 evidence/implementation/review 결과 |

파일명과 위치는 프로젝트 증거 관리 제안이다. Lab의 예시 ACCEPTED/MITIGATED 문장을 실제 수정·검증 없이 복사하지 않는다. 이번 보완 작업은 분석·문서 수정만 수행했고 애플리케이션 코드는 변경하지 않았다.
