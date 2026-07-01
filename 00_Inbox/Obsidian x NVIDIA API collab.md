## 11. MVP 개발 순서

### Phase 1 — Codex 로그 수집

목표는 “Codex 작업 요약이 항상 Obsidian Inbox에 들어오는 것”입니다.

작업:

```
1. Codex 세션 종료 Hook 생성2. ~/.codex/working_list/YYYY_MM_DD/ 에 작업 로그 저장3. Obsidian 00_Inbox/codex_logs/YYYY-MM-DD/ 로 복사4. YAML frontmatter 포함5. 파일명에 날짜, feature-name 포함
```

완료 기준:

```
Codex 작업 1회 종료 시 Obsidian 00_Inbox에 Markdown 1개가 자동 생성된다.
```

---

### Phase 2 — LLM 정리 제안 생성

목표는 “Inbox 로그를 읽고 정리 제안 파일을 만드는 것”입니다.

작업:

```
1. NVIDIA API Key 발급2. Python OpenAI SDK 호환 호출 구성3. 00_Inbox/codex_logs 하위 파일 스캔4. 처리되지 않은 파일만 LLM에 전달5. 00_Inbox/_review 에 proposal 생성6. manifest.sqlite에 처리 이력 저장
```

완료 기준:

```
원본 Codex 로그 1개당 정리 제안 Markdown 1개가 생성된다.
```

---

### Phase 3 — 승인 후 구조화 반영

목표는 “리더님이 확인한 proposal을 실제 폴더에 반영하는 것”입니다.

처음에는 완전 자동 이동보다 아래 방식이 안전합니다.

```
status: review → approved 로 바꾸면스크립트가 실제 노트에 append/create
```

예시:

```
---type: llm_organization_proposalstatus: approved---
```

완료 기준:

```
approved proposal만 01_Daily, 10_Projects, 50_Decisions로 반영된다.
```

---

### Phase 4 — RAG 인덱싱

목표는 “정리된 Obsidian 노트를 검색 가능한 벡터 DB로 만드는 것”입니다.

작업:

```
1. Markdown 파일 스캔2. frontmatter + heading 기준 chunking3. NVIDIA embedding API 호출4. Chroma local persistent DB 저장5. 변경 파일만 재인덱싱
```

완료 기준:

```
질문을 입력하면 관련 Obsidian 노트 chunk가 검색된다.
```

---

### Phase 5 — RAG 질의응답 CLI

목표는 “터미널에서 내 Obsidian에 질문하면 근거 기반 답변이 나오는 것”입니다.

명령 예시:

```
python scripts/ask_vault.py "Stage 1-1에서 universe 수집 정책은 어떻게 정했어?"
```

출력 예시:

```
## AnswerStage 1-1에서는 universe 수집을 기본적으로 fail-closed로 유지하기로 했습니다...## Sources1. 10_Projects/INNO_KIS_Trading/Development Log.md > 2026-06-302. 50_Decisions/INNO_KIS_Trading/decision-2026-06-30-universe-policy.md
```