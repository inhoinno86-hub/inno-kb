# INNO Obsidian AI

Codex 작업 로그 Markdown을 Obsidian 정리 제안으로 바꾸고, 승인 후 append-only로 반영하고, 이후 Chroma 기반 RAG 검색까지 연결하는 로컬 파이프라인이다.

## Phase 3 목표

Phase 3는 Phase 2/2.5에 이미 구현된 기능을 자동 운영 루프로 묶는 단계다.

- NVIDIA NIM 기반 proposal 생성
- `status: approved` proposal만 append-only 반영
- changed note만 incremental reindex
- operation log / project dashboard 자동 갱신
- 기본 모드는 dry-run, 기본 인덱싱 범위는 path-prefix 기반

## Phase 4 목표

Phase 4는 Phase 3 파이프라인을 실제 운영 가능한 수준으로 단단하게 만드는 단계다.

- 실행 전 preflight validator 추가
- live write 전 위험 요소 자동 점검
- read-only status summary 제공
- 제한된 live rollout runbook 문서화
- cron/systemd는 예시만 제공하고 자동 등록은 하지 않음
- 기존 Phase 3 동작을 깨지 않도록 테스트 보강

## Phase 2.5 목표

Phase 2.5는 기능 확장보다 운영 안정화가 목적이다.

- 전체 vault 재임베딩 대신 `path-prefix` 기반 점진 인덱싱
- 변경 파일만 재인덱싱하고 unchanged 파일은 skip
- manifest에 file/chunk hash, model, collection, status 기록
- 삭제되거나 정책상 제외된 파일 cleanup
- `ask_vault.py` 답변을 `Answer / Sources / Evidence` 형식으로 고정
- `.inno_rag/logs/` audit log로 인덱싱 가시성 강화

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp config/obsidian_ai.example.yaml config/obsidian_ai.yaml
export NVIDIA_API_KEY=...
```

`.env`는 로컬 전용으로 쓰고 커밋하지 않는다.
`config/obsidian_ai.yaml`도 로컬 전용 설정 파일이며 `.gitignore`에 포함한다.

## NVIDIA API 설정

실제 proposal 생성, embedding, 질의응답은 `NVIDIA_API_KEY`가 필요하다. API key는 환경변수로만 읽고 config 파일에는 넣지 않는다.

```bash
export NVIDIA_API_KEY=nvapi-...
```

키가 없으면 NVIDIA 연동 명령은 아래 메시지로 실패해야 한다.

```text
NVIDIA_API_KEY is not set. Export NVIDIA_API_KEY before using NVIDIA-backed commands.
```

## 설정

기본 예시는 [config/obsidian_ai.example.yaml](/home/inno/문서/Obsidian%20Vault/Documents/Obsidian/INNO-KB/config/obsidian_ai.example.yaml) 에 있다.

핵심 값:

- `vault_path`
- `inbox.codex_logs`
- `inbox.review`
- `inbox.processed`
- `nvidia.base_url`
- `nvidia.llm_model`
- `nvidia.embedding_model`
- `nvidia.rerank_model`
- `indexing.default_include_original_inbox_logs`
- `indexing.include_patterns`
- `indexing.exclude_patterns`
- `indexing.note_type_policy`
- `embedding.batch_size`
- `embedding.max_retries`
- `embedding.retry_backoff_seconds`
- `embedding.timeout_seconds`
- `embedding.max_chunk_chars`
- `rag.persist_dir`
- `rag.chunk_size`
- `rag.chunk_overlap`
- `rag.top_k`
- `rag.rerank_top_k`
- `rag.index_raw_codex_logs`
- `rag.answer_format`
- `rag.max_evidence_distance`
- `rag.require_sources`
- `safety.dry_run`
- `safety.require_approval_for_apply`
- `safety.append_only`
- `safety.redact_secrets`
- `automation.max_files_per_run`
- `automation.allow_full_vault_index`
- `automation.default_index_path_prefixes`
- `operation_log.destination`
- `dashboard.path`

현재 기본 embedding 모델 `nvidia/nv-embedqa-e5-v5` 기준으로 `rag.chunk_size`는 `500`부터 시작하는 편이 안전하다. 더 크게 잡으면 embedding API의 최대 token 제한에 걸릴 수 있다.

## 사용

정리 제안 스캔만:

```bash
python3 scripts/organize_codex_inbox_with_nvidia.py --config config/obsidian_ai.yaml
```

실제 proposal 생성:

```bash
python3 scripts/organize_codex_inbox_with_nvidia.py --config config/obsidian_ai.yaml --write
```

실제 쓰기 전에 반드시 dry-run을 먼저 실행한다.

승인된 proposal 반영:

```bash
python3 scripts/apply_approved_proposals.py --config config/obsidian_ai.yaml --write
```

Phase 2.5에서는 full vault 인덱싱보다 프로젝트별 점진 확장을 권장한다.

증분 인덱싱 dry-run + stats:

```bash
python3 scripts/index_obsidian_vault.py \
  --config config/obsidian_ai.yaml \
  --path-prefix "10_Projects/INNO_KIS_Trading/06_Logs" \
  --dry-run \
  --stats
```

특정 경로 live 인덱싱:

```bash
python3 scripts/index_obsidian_vault.py \
  --config config/obsidian_ai.yaml \
  --path-prefix "10_Projects/INNO_KIS_Trading/06_Logs" \
  --write
```

삭제/제외 파일 cleanup dry-run:

```bash
python3 scripts/index_obsidian_vault.py \
  --config config/obsidian_ai.yaml \
  --path-prefix "10_Projects/INNO_KIS_Trading" \
  --cleanup-missing \
  --dry-run
```

실패 파일만 재시도:

```bash
python3 scripts/index_obsidian_vault.py \
  --config config/obsidian_ai.yaml \
  --path-prefix "10_Projects/INNO_KIS_Trading" \
  --failed-only \
  --write
```

질의:

```bash
python3 scripts/ask_vault.py \
  --config config/obsidian_ai.yaml \
  "Phase 2에서 append-only 정책은 어떻게 검증됐어?"
```

`ask_vault.py` 출력은 항상 아래 형식을 따른다.

```markdown
## Answer

...

## Sources

1. path/to/file.md > Heading

## Evidence

* top_k: ...
* rerank_used: ...
* collection: ...
* model: ...
```

근거가 부족하면 아래처럼 반환한다.

```markdown
## Answer

근거 부족

## Sources

* none

## Evidence

* reason: insufficient_relevant_context
* top_k: ...
* threshold: ...
```

## Phase 3 자동 운영

기본 정책:

- `--write` 없이는 어떤 파일도 수정하지 않는다.
- full vault index는 기본 차단이다.
- 자동 운영 기본 권장 모드는 `--dry-run` 또는 `--organize-only`.
- approved apply 자동화는 `status: approved` proposal만 처리한다.

Phase 4 preflight validator:

```bash
python3 scripts/validate_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --check-all
```

read-only status summary:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --status
```

전체 dry-run:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --dry-run \
  --stats
```

신규 Codex log proposal 생성만:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --organize-only \
  --write \
  --max-files 5
```

approved proposal 반영만:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --apply-only \
  --write
```

특정 프로젝트 범위 incremental index:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --index-only \
  --write \
  --path-prefix "10_Projects/INNO_KIS_Trading"
```

summary/dashboard 갱신만:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --summary-only \
  --write
```

cron/systemd에서 호출할 wrapper:

```bash
scripts/run_obsidian_ai_pipeline.sh --dry-run
```

safe rollout 최소 순서:

1. `scripts/validate_obsidian_ai_pipeline.py --config config/obsidian_ai.yaml --check-all`
2. `scripts/run_obsidian_ai_pipeline.py --config config/obsidian_ai.yaml --dry-run --stats`
3. `scripts/run_obsidian_ai_pipeline.py --config config/obsidian_ai.yaml --organize-only --write --max-files 1 --stats`
4. Obsidian에서 proposal 검토 후 `status: approved`만 수동 변경
5. `scripts/run_obsidian_ai_pipeline.py --config config/obsidian_ai.yaml --apply-only --write --stats`
6. `scripts/run_obsidian_ai_pipeline.py --config config/obsidian_ai.yaml --index-only --write --path-prefix "10_Projects/INNO_KIS_Trading" --stats`

운영 전 체크리스트:

- live write 전 반드시 preflight + full dry-run을 먼저 실행한다.
- full vault index는 기본 금지이며 `--force-full-index`와 config 허용이 둘 다 있어야만 가능하다.
- 기본 운영 범위는 `path-prefix`로 제한한다.
- `status: approved`가 아닌 proposal은 apply하지 않는다.
- `config/obsidian_ai.yaml`, `.env`, `.venv/`, `.inno_rag/`, `logs/`, Chroma DB는 커밋하지 않는다.

권장 운영 모드:

- `--dry-run --stats`
- `--organize-only --write --max-files 1`
- `--apply-only --write`
- `--index-only --write --path-prefix ...`

금지 또는 비권장 운영 모드:

- default full vault live index
- 승인되지 않은 proposal apply
- 첫 rollout에서 넓은 범위 write
- secret 값을 CLI, 문서, 로그에 직접 남기는 방식

운영 참고 문서:

- [docs/phase-3-automation.md](/home/inno/문서/Obsidian%20Vault/Documents/Obsidian/INNO-KB/docs/phase-3-automation.md)
- [docs/phase-4-operational-hardening.md](/home/inno/문서/Obsidian%20Vault/Documents/Obsidian/INNO-KB/docs/phase-4-operational-hardening.md)

## End-to-End 검증

1. `python3 scripts/organize_codex_inbox_with_nvidia.py --config config/obsidian_ai.yaml`
2. `export NVIDIA_API_KEY=...`
3. `python3 scripts/organize_codex_inbox_with_nvidia.py --config config/obsidian_ai.yaml --write`
4. proposal frontmatter에서 `status: approved`로 변경
5. `python3 scripts/apply_approved_proposals.py --config config/obsidian_ai.yaml --write`
6. 같은 apply 명령을 다시 실행해 중복 append가 없는지 확인
7. `python3 scripts/index_obsidian_vault.py --config config/obsidian_ai.yaml --path-prefix "10_Projects/INNO_KIS_Trading/06_Logs" --write`
8. 비용/검증 목적이면 `--path-prefix`로 대상 노트를 제한 가능
9. 새 프로세스에서 `python3 scripts/ask_vault.py "질문" --config config/obsidian_ai.yaml`

## 동작 원칙

- 원본 `00_Inbox/codex_logs`는 수정하지 않는다.
- proposal은 `00_Inbox/_review`에 생성한다.
- `status: approved` proposal만 실제 노트에 반영한다.
- 반영은 새 파일 생성 또는 `## YYYY-MM-DD - {feature}` 섹션 append만 한다.
- 민감 정보는 NVIDIA API 전송 전에 redaction 한다.
- pipeline operation log는 append-only다.
- dashboard는 marker 내부만 자동 갱신한다.
- 처리 이력과 인덱싱 해시는 `.inno_rag/manifest.sqlite`에 저장한다.
- 인덱싱 audit log는 `.inno_rag/logs/`에 JSONL로 남는다.
- `config/obsidian_ai.yaml`, `.env`, `.venv/`, `.inno_rag/`, Chroma DB, `logs/`, live E2E 산출물은 커밋하지 않는다.
- 로컬 산출물 제외 규칙은 `.gitignore`에서 유지한다.
