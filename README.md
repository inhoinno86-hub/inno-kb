# INNO Obsidian AI

Codex 작업 로그 Markdown을 Obsidian 정리 제안으로 바꾸고, 승인 후 append-only로 반영하고, 이후 Chroma 기반 RAG 검색까지 연결하는 로컬 파이프라인이다.

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

실제 proposal 생성, embedding, 질의응답은 `NVIDIA_API_KEY`가 필요하다.

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
- `rag.persist_dir`
- `rag.chunk_size`
- `rag.chunk_overlap`
- `rag.top_k`
- `rag.rerank_top_k`
- `rag.index_raw_codex_logs`
- `safety.dry_run`
- `safety.require_approval_for_apply`
- `safety.append_only`
- `safety.redact_secrets`

현재 기본 embedding 모델 `nvidia/nv-embedqa-e5-v5` 기준으로 `rag.chunk_size`는 `500`부터 시작하는 편이 안전하다. 더 크게 잡으면 embedding API의 최대 token 제한에 걸릴 수 있다.

## 사용

정리 제안 스캔만:

```bash
python scripts/organize_codex_inbox_with_nvidia.py --config config/obsidian_ai.yaml
```

실제 proposal 생성:

```bash
python scripts/organize_codex_inbox_with_nvidia.py --config config/obsidian_ai.yaml --write
```

실제 쓰기 전에 반드시 dry-run을 먼저 실행한다.

승인된 proposal 반영:

```bash
python scripts/apply_approved_proposals.py --config config/obsidian_ai.yaml --write
```

Vault 인덱싱:

```bash
python scripts/index_obsidian_vault.py --config config/obsidian_ai.yaml --write
```

특정 경로만 인덱싱해서 검증하거나 비용을 제한하려면:

```bash
python scripts/index_obsidian_vault.py \
  --config config/obsidian_ai.yaml \
  --path-prefix "10_Projects/INNO_KIS_Trading/06_Logs/Phase 2 Live E2E Verification Sandbox.md" \
  --write
```

질의:

```bash
python scripts/ask_vault.py "phase 1에서 append-only 제약은 어떻게 다뤘나?" --config config/obsidian_ai.yaml
```

## End-to-End 검증

1. `python scripts/organize_codex_inbox_with_nvidia.py --config config/obsidian_ai.yaml`
2. `export NVIDIA_API_KEY=...`
3. `python scripts/organize_codex_inbox_with_nvidia.py --config config/obsidian_ai.yaml --write`
4. proposal frontmatter에서 `status: approved`로 변경
5. `python scripts/apply_approved_proposals.py --config config/obsidian_ai.yaml --write`
6. 같은 apply 명령을 다시 실행해 중복 append가 없는지 확인
7. `python scripts/index_obsidian_vault.py --config config/obsidian_ai.yaml --write`
8. 비용/검증 목적이면 `--path-prefix`로 대상 노트를 제한 가능
9. 새 프로세스에서 `python scripts/ask_vault.py "질문" --config config/obsidian_ai.yaml`

## 동작 원칙

- 원본 `00_Inbox/codex_logs`는 수정하지 않는다.
- proposal은 `00_Inbox/_review`에 생성한다.
- `status: approved` proposal만 실제 노트에 반영한다.
- 반영은 새 파일 생성 또는 `## YYYY-MM-DD - {feature}` 섹션 append만 한다.
- 민감 정보는 NVIDIA API 전송 전에 redaction 한다.
- 처리 이력과 인덱싱 해시는 `.inno_rag/manifest.sqlite`에 저장한다.
