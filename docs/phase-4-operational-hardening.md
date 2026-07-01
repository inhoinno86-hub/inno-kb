# Phase 4: Operational Hardening & Safe Live Rollout

## 목적

Phase 4는 Phase 3에서 만든 organizer/apply/index 자동 운영 루프를 실제 운영 가능한 수준으로 안정화하는 단계다.

- 실행 전 preflight 검증을 추가한다.
- live write 전에 위험 요소를 자동 점검한다.
- 최근 run 상태와 실패 항목을 사람이 빠르게 읽을 수 있게 만든다.
- 제한된 live rollout 절차를 문서화한다.
- cron/systemd는 예시만 제공하고 실제 등록은 하지 않는다.

## Phase 3와의 관계

Phase 3는 pipeline orchestration을 만들었다. Phase 4는 그 기능을 크게 넓히지 않고, 실운영 전환 전에 안전장치와 운영 문서를 보강한다.

- 원본 `00_Inbox/codex_logs`는 수정하지 않는다.
- proposal 생성은 자동화 가능하지만 apply는 `status: approved`만 허용한다.
- dashboard는 marker 내부만 갱신한다.
- append-only 원칙을 유지한다.
- full vault index는 기본 차단한다.

## 운영 전 Preflight

먼저 validator를 실행한다.

```bash
.venv/bin/python scripts/validate_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --check-all
```

validator는 다음을 점검한다.

- config 존재 여부와 schema load 가능 여부
- safe default 여부 (`dry_run`, `allow_full_vault_index: false`, default path-prefix)
- `NVIDIA_API_KEY` 존재 여부만 확인하고 값은 출력하지 않음
- `00_Inbox/codex_logs`, proposal dir, dashboard path, operation log path 상태
- dashboard marker 설정
- `.env`, `.venv`, `.inno_rag`, Chroma DB, live config의 git ignore/tracked 위험
- shell wrapper의 secret echo 금지 여부
- read-only status CLI 실행 가능 여부

JSON 출력이 필요하면:

```bash
.venv/bin/python scripts/validate_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --check-all \
  --json
```

추가 상태 확인:

```bash
.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --status
```

## Safe Rollout 순서

아래 순서를 유지한다.

```bash
# 1. Preflight
.venv/bin/python scripts/validate_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --check-all

# 2. Full dry-run
.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --dry-run \
  --stats

# 3. Narrow proposal generation
.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --organize-only \
  --write \
  --max-files 1 \
  --stats

# 4. Human review in Obsidian
# Change proposal status from review to approved manually.

# 5. Approved apply
.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --apply-only \
  --write \
  --stats

# 6. Changed-note indexing only
.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --index-only \
  --write \
  --path-prefix "10_Projects/INNO_KIS_Trading" \
  --stats

# 7. Dashboard/log update check
.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --summary-only \
  --dry-run \
  --stats
```

## 최초 Live Smoke Test

최초 live write는 넓게 하지 않는다.

- `--organize-only --write --max-files 1`만 허용한다.
- apply는 사람이 `status: approved`를 넣은 뒤에만 진행한다.
- 첫 run에서 full vault index는 금지한다.
- 실제 live write가 필요하면 1개 파일만 대상으로 제한한다.

## Proposal 검토 절차

proposal 검토 시 아래를 본다.

- Summary가 원본 working_list 사실만 반영하는지
- Suggested Destination Notes 경로가 올바른지
- Commands / Tests / Decisions / TODO가 과장 없이 원문 근거를 따르는지
- Human Review Required 항목이 해소됐는지

`status: approved`로 바꿀 기준:

- destination note가 안전하다
- append-only 반영이 기존 문맥을 훼손하지 않는다
- 사실 관계가 working_list와 일치한다
- 민감정보가 노출되지 않는다

## Approved Apply 및 Reindex

approved apply:

```bash
.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --apply-only \
  --write \
  --stats
```

changed-note reindex:

```bash
.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --index-only \
  --write \
  --path-prefix "10_Projects/INNO_KIS_Trading" \
  --stats
```

실패 항목만 재시도:

```bash
.venv/bin/python scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --index-only \
  --write \
  --path-prefix "10_Projects/INNO_KIS_Trading" \
  --failed-only \
  --stats
```

## Dashboard / Log / 실패 확인

확인할 주요 파일:

- operation log note
- project dashboard note
- `.inno_rag/manifest.sqlite`
- `.inno_rag/logs/index-*.jsonl`
- `logs/obsidian_ai_pipeline_*.log`
- `00_Inbox/_review/**/*.proposal.md`

dashboard는 marker 내부만 갱신한다. marker 밖 사용자 작성 내용은 수정하지 않는다.

실패 시 먼저 볼 것:

1. validator output
2. wrapper 로그
3. index audit log
4. proposal frontmatter/status
5. dashboard marker 존재 여부

## Full Vault Index 금지 이유

- 비용과 시간이 크다.
- 잘못된 범위 확장 시 live rollout 리스크가 커진다.
- Phase 4의 목적은 전체 재색인이 아니라 안전한 점진 운영이다.

full vault index는 아래 둘 다 있을 때만 예외적으로 허용한다.

- `--force-full-index`
- config의 `automation.allow_full_vault_index: true`

기본 운영은 path-prefix 기반으로 유지한다.

## Path-Prefix 기반 확장 전략

권장 순서:

1. `10_Projects/INNO_KIS_Trading/06_Logs`
2. `10_Projects/INNO_KIS_Trading`
3. 다른 프로젝트별 prefix 추가

한 번에 전체 vault로 넓히지 않는다.

## Cron / systemd 예시

실제 등록은 하지 않는다. 문서 예시만 유지한다.

안전한 cron 예시:

```cron
# Dry-run health check only
0 9 * * * cd "/home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB" && .venv/bin/python scripts/run_obsidian_ai_pipeline.py --config config/obsidian_ai.yaml --dry-run --stats
```

보수적 cron 예시:

```cron
# Narrow proposal generation only
30 9 * * * cd "/home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB" && .venv/bin/python scripts/run_obsidian_ai_pipeline.py --config config/obsidian_ai.yaml --organize-only --write --max-files 5 --stats
```

주의:

- apply 자동화는 `status: approved` proposal만 처리한다.
- full vault index 자동화 예시는 제공하지 않는다.
- `NVIDIA_API_KEY` 값은 cron line이나 문서에 직접 쓰지 않는다.

systemd user service 예시:

`~/.config/systemd/user/obsidian-ai-pipeline-dry-run.service`

```ini
[Unit]
Description=Obsidian AI pipeline dry-run

[Service]
Type=oneshot
WorkingDirectory=/home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB
ExecStart=/home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB/.venv/bin/python /home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB/scripts/run_obsidian_ai_pipeline.py --config /home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB/config/obsidian_ai.yaml --dry-run --stats
```

`~/.config/systemd/user/obsidian-ai-pipeline-dry-run.timer`

```ini
[Unit]
Description=Run Obsidian AI pipeline dry-run

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

등록 전 체크리스트:

- `.venv/bin/python` 존재
- `config/obsidian_ai.yaml` 존재
- `NVIDIA_API_KEY`가 shell/session에만 설정됨
- preflight 통과
- dry-run 통과
- 첫 live rollout은 이미 수동으로 `--max-files 1` 확인 완료

## 자동화 권장 순서

1. 수동 preflight
2. 수동 full dry-run
3. 제한된 `organize-only --write --max-files 1`
4. proposal 수동 승인
5. approved apply
6. changed-note reindex
7. 그 다음에만 dry-run cron
8. 마지막으로 제한된 organize-only cron

자동화 금지 조건:

- preflight FAIL 존재
- dashboard marker 없음
- git ignore 위험 존재
- `NVIDIA_API_KEY` 미설정
- full vault index를 기본 자동화로 넣으려는 경우
- append-only 원칙을 지킬 수 없는 수동 수정이 필요한 경우

## Append-Only Correction 원칙

rollback 대신 correction note를 쓴다.

- 이미 append된 내용은 삭제/덮어쓰기하지 않는다.
- 잘못 반영됐으면 새 correction section 또는 새 note로 바로잡는다.
- dashboard와 operation log는 append/update 규칙을 지키되 사용자 본문은 건드리지 않는다.

## 민감정보 유출 방지 체크리스트

- `NVIDIA_API_KEY`는 환경변수에서만 읽는다.
- API key 값은 로그, proposal, dashboard, README, runbook에 넣지 않는다.
- wrapper나 cron/systemd 예시에 실제 secret 값을 넣지 않는다.
- LLM 전송 전 redaction이 유지되는지 확인한다.

## Git Commit 전 확인

아래는 커밋 금지 대상이다.

- `config/obsidian_ai.yaml`
- `.env`
- `.venv/`
- `.inno_rag/`
- Chroma DB live 산출물
- `logs/`
- live smoke 결과 파일과 임시 산출물

커밋 전 점검:

```bash
git status --short
git check-ignore -v config/obsidian_ai.yaml .env .venv .inno_rag
```
