# Phase 3 Automation

## 목적

Phase 3는 Phase 2/2.5에 이미 구현된 organizer, approved apply, Chroma RAG, incremental indexing hardening을 반복 가능한 자동 운영 파이프라인으로 묶는다.

- 원본 `00_Inbox/codex_logs`는 수정하지 않는다.
- proposal 생성은 자동화 가능하지만 실제 반영은 `status: approved` proposal만 허용한다.
- append-only 원칙을 유지한다.
- 기본 실행은 dry-run이다.
- full vault index 자동 실행은 권장하지 않는다.
- path-prefix 기반 점진 인덱싱을 권장한다.

## 수동 실행

기본 dry-run:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --dry-run \
  --stats
```

organize-only:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --organize-only \
  --write \
  --max-files 5
```

apply-only:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --apply-only \
  --write
```

index-only:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --index-only \
  --write \
  --path-prefix "10_Projects/INNO_KIS_Trading"
```

summary/dashboard update only:

```bash
python3 scripts/run_obsidian_ai_pipeline.py \
  --config config/obsidian_ai.yaml \
  --summary-only \
  --write
```

wrapper 사용:

```bash
scripts/run_obsidian_ai_pipeline.sh --dry-run
```

## 자동 실행 권장 모드

- 기본 권장: `--dry-run`
- 보수적 자동화: `--organize-only --write`
- approved apply 자동화: reviewer가 `status: approved`를 명시적으로 남기는 워크플로에서만 허용

`--organize-only`를 권장하는 이유:

- proposal만 생성하고 실제 노트는 건드리지 않는다.
- reviewer가 destination, summary, TODO를 확인한 뒤 승인할 수 있다.
- 과도한 live indexing 비용 없이 후보만 계속 축적할 수 있다.

approved apply 자동화의 안전 조건:

- `status: approved` proposal만 처리한다.
- `review`, `rejected`, `applied`는 skip한다.
- destination note는 append-only로만 수정한다.
- 기존 heading이 이미 있으면 중복 append하지 않는다.

## cron 예시

```cron
15 23 * * * cd "/home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB" && NVIDIA_API_KEY=... scripts/run_obsidian_ai_pipeline.sh --organize-only --write
```

더 안전한 시작점:

```cron
15 23 * * * cd "/home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB" && NVIDIA_API_KEY=... scripts/run_obsidian_ai_pipeline.sh --dry-run
```

## systemd user timer 예시

`~/.config/systemd/user/obsidian-ai-pipeline.service`

```ini
[Unit]
Description=Obsidian AI pipeline

[Service]
Type=oneshot
WorkingDirectory=/home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB
Environment=NVIDIA_API_KEY=...
ExecStart=/home/inno/문서/Obsidian Vault/Documents/Obsidian/INNO-KB/scripts/run_obsidian_ai_pipeline.sh --organize-only --write
```

`~/.config/systemd/user/obsidian-ai-pipeline.timer`

```ini
[Unit]
Description=Run Obsidian AI pipeline nightly

[Timer]
OnCalendar=*-*-* 23:15:00
Persistent=true

[Install]
WantedBy=timers.target
```

등록 예시:

```bash
systemctl --user daemon-reload
systemctl --user enable --now obsidian-ai-pipeline.timer
systemctl --user list-timers | grep obsidian-ai-pipeline
```

실제 등록은 수동으로만 수행한다.

## NVIDIA_API_KEY 처리

- `NVIDIA_API_KEY`는 환경변수에서만 읽는다.
- config 파일이나 proposal, operation log, dashboard에 넣지 않는다.
- shell wrapper는 값 자체를 출력하지 않는다.

예시:

```bash
export NVIDIA_API_KEY=nvapi-...
```

## `.venv` 활성화

직접 실행:

```bash
source .venv/bin/activate
```

wrapper는 `.venv` 존재 여부를 먼저 확인한 뒤 내부에서 활성화한다.

## 실패 로그 확인

- wrapper 실행 로그: `logs/obsidian_ai_pipeline_YYYYMMDD_HHMMSS.log`
- indexing audit log: `.inno_rag/logs/index-*.jsonl`
- proposal/apply/index 결과는 CLI stdout/stderr에도 출력된다.

## 자동화 범위 제한 전략

- `--max-files`로 한 번에 처리할 로그 수를 제한한다.
- `--path-prefix`로 프로젝트 단위 인덱싱만 허용한다.
- `--no-llm`으로 candidate 탐지만 먼저 확인할 수 있다.
- `--failed-only`로 이전 failed index만 재시도할 수 있다.

권장 전략:

1. 먼저 `--dry-run --stats`
2. 그다음 `--organize-only --write --max-files N`
3. 승인된 proposal이 쌓이면 `--apply-only --write`
4. 대규모 live embedding 대신 `--index-only --path-prefix ...`

## full vault index를 권장하지 않는 이유

- NVIDIA embedding 호출 수와 처리 시간이 커진다.
- 전체 vault 재색인은 운영 루프 반복성을 떨어뜨린다.
- 실제 운영에서는 changed note와 path-prefix 단위가 비용과 안정성 면에서 유리하다.

`allow_full_vault_index: false`인 기본 설정에서는 full index 요청이 실패한다.

## path-prefix 기반 점진 확장

기본 권장 prefix:

```yaml
automation:
  default_index_path_prefixes:
    - "10_Projects/INNO_KIS_Trading"
```

점진 확장 예시:

1. `10_Projects/INNO_KIS_Trading/06_Logs`
2. `10_Projects/INNO_KIS_Trading`
3. 필요 시 다른 프로젝트 prefix 추가

full vault live embedding을 기본값으로 켜는 방식은 피한다.

## 운영 중 확인할 파일

- `config/obsidian_ai.yaml`
- `00_Inbox/_review/**/*.proposal.md`
- `.inno_rag/manifest.sqlite`
- `.inno_rag/logs/index-*.jsonl`
- operation log destination note
- project dashboard note

## Git에 커밋하면 안 되는 파일

- `config/obsidian_ai.yaml`
- `.env`
- `.venv/`
- `.inno_rag/`
- `logs/`
- Chroma DB live 산출물

## 장애 시 복구

1. dry-run으로 현재 대상과 stats를 다시 확인한다.
2. `review` proposal을 수동으로 점검한다.
3. `applied` proposal과 destination note heading 중복 여부를 확인한다.
4. failed index가 있으면 `--failed-only` 또는 좁은 `--path-prefix`로 재시도한다.
5. dashboard는 marker 내부만 다시 생성하면 되고, marker 밖 사용자 내용은 보존된다.
