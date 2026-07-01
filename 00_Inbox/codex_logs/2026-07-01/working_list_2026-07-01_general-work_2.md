---
type: codex_session_log
source: codex
project: INNO_KIS_Trading
feature: general-work
created: 2026-07-01
status: inbox
---

# Codex Working List - 2026-07-01 - general-work

## 1. Goal

- * Phase 1-29: DART corpCode XML/ZIP 공식 다운로드 또는 verified local ZIP/XML 처리 workflow를 수동 검증한다.

## 2. Changed Files

| File | Change Summary |
|---|---|
| `src/inno_kis_trading/data/dart.py` | Updated via apply_patch |
| `scripts/build_dart_corp_mapping.py` | Updated via apply_patch |
| `tests/test_dart.py` | Updated via apply_patch |
| `tests/test_build_dart_corp_mapping.py` | Updated via apply_patch |
| `docs/stage1-dart-corp-mapping.md` | Updated via apply_patch |
| `docs/stage1-dart-ingestion.md` | Updated via apply_patch |
| `docs/stage1-financial-input-workflow.md` | Updated via apply_patch |
| `docs/stage1-verified-input-contracts.md` | Updated via apply_patch |
| `scripts/build_financial_metrics.py` | Updated via apply_patch |
| `tests/test_build_financial_metrics.py` | Updated via apply_patch |
| `scripts/build_market_input.py` | Updated via apply_patch |
| `tests/test_build_market_input.py` | Updated via apply_patch |
| `docs/stage1-market-input-workflow.md` | Updated via apply_patch |
| `docs/stage1-kis-market-data.md` | Updated via apply_patch |
| `scripts/run_screener.py` | Updated via apply_patch |
| `tests/test_pipeline.py` | Updated via apply_patch |
| `docs/stage1-real-dry-run.md` | Updated via apply_patch |
| `docs/stage1-real-dry-run-checklist.md` | Updated via apply_patch |
| `docs/stage1-output.md` | Updated via apply_patch |

## 3. Commands Run

```bash
pwd
git status --short
git log --oneline -25
find . -maxdepth 4 -type f | sort | sed 's#^\./##' | head -450
.venv/bin/python -m pytest
git ls-files data/raw data/interim data/processed reports
git status --short --ignored data/raw data/interim data/processed reports | head -150
git ls-files data/processed/stage1/universe_20260701.csv data/processed/stage1/universe_20260701.metadata.json
git check-ignore -v data/processed/stage1/universe_20260701.csv || true
git check-ignore -v data/processed/stage1/universe_20260701.metadata.json || true
sed -n '1,260p' scripts/build_dart_corp_mapping.py
sed -n '1,320p' src/inno_kis_trading/data/dart.py
sed -n '1,260p' scripts/build_financial_metrics.py
sed -n '1,240p' docs/stage1-dart-corp-mapping.md
sed -n '1,260p' docs/stage1-dart-ingestion.md
sed -n '1,260p' docs/stage1-financial-input-workflow.md
sed -n '1,260p' docs/stage1-verified-input-contracts.md
sed -n '1,260p' tests/test_build_dart_corp_mapping.py
rg -n "corp mapping|corp_code|validate-mapping|check-readiness|allow-write|local-input|mapping" tests src scripts docs -g '!data/**'
sed -n '300,380p' src/inno_kis_trading/data/dart.py
sed -n '240,460p' scripts/build_financial_metrics.py
sed -n '1,320p' scripts/build_market_input.py
sed -n '1,340p' src/inno_kis_trading/data/kis_market.py
sed -n '1,320p' scripts/run_screener.py
sed -n '1,360p' src/inno_kis_trading/screener/pipeline.py
sed -n '1,320p' src/inno_kis_trading/screener/output.py
sed -n '1,260p' tests/test_build_financial_metrics.py
sed -n '1,260p' tests/test_build_market_input.py
sed -n '1,320p' tests/test_smoke.py
sed -n '420,560p' tests/test_dart.py
sed -n '1,220p' tests/test_dart.py
rg -n "metadata" tests/test_dart.py tests/test_build_dart_corp_mapping.py src/inno_kis_trading/data/dart.py scripts/build_dart_corp_mapping.py
sed -n '1,140p' src/inno_kis_trading/data/dart.py
sed -n '140,260p' src/inno_kis_trading/data/dart.py
sed -n '260,360p' src/inno_kis_trading/data/dart.py
sed -n '360,440p' src/inno_kis_trading/data/dart.py
sed -n '700,740p' src/inno_kis_trading/data/dart.py
.venv/bin/python -m pytest tests/test_dart.py tests/test_build_dart_corp_mapping.py
.venv/bin/python scripts/build_dart_corp_mapping.py --help
.venv/bin/python scripts/build_dart_corp_mapping.py --check-readiness
git diff -- scripts/build_dart_corp_mapping.py src/inno_kis_trading/data/dart.py tests/test_build_dart_corp_mapping.py tests/test_dart.py docs/stage1-dart-corp-mapping.md docs/stage1-dart-ingestion.md docs/stage1-financial-input-workflow.md docs/stage1-verified-input-contracts.md
git diff -- AGENTS.md
git add docs/stage1-dart-corp-mapping.md docs/stage1-dart-ingestion.md docs/stage1-financial-input-workflow.md docs/stage1-verified-input-contracts.md scripts/build_dart_corp_mapping.py src/inno_kis_trading/data/dart.py tests/test_build_dart_corp_mapping.py tests/test_dart.py && git commit -m "stage1: validate dart corp code workflow"
.venv/bin/python -m pytest tests/test_build_dart_corp_mapping.py tests/test_dart.py
.venv/bin/python scripts/build_dart_corp_mapping.py --check-readiness --universe-input data/processed/stage1/universe_20260701.csv --mapping-input data/interim/stage1/missing-mapping.csv
git diff -- scripts/build_dart_corp_mapping.py tests/test_build_dart_corp_mapping.py docs/stage1-dart-corp-mapping.md docs/stage1-financial-input-workflow.md
git add docs/stage1-dart-corp-mapping.md docs/stage1-financial-input-workflow.md scripts/build_dart_corp_mapping.py tests/test_build_dart_corp_mapping.py && git commit -m "stage1: measure dart mapping coverage"
sed -n '1,360p' tests/test_build_financial_metrics.py
sed -n '1,260p' docs/stage1-dart-account-mapping.md
sed -n '1,220p' scripts/build_financial_metrics.py
sed -n '220,420p' scripts/build_financial_metrics.py
.venv/bin/python -m pytest tests/test_build_financial_metrics.py tests/test_dart.py
.venv/bin/python scripts/build_financial_metrics.py --help
.venv/bin/python scripts/build_financial_metrics.py --check-readiness --api --universe-input data/processed/stage1/universe_20260701.csv
.venv/bin/python scripts/build_financial_metrics.py --local-raw-input /tmp/nonexistent.json --validate-only
tmpdir=$(mktemp -d); cat > "$tmpdir/dart-wrapper.json" <<'EOF'
{
  "request": {
    "corp_code": "12345678",
    "ticker": "0A0001",
    "business_year": "2025",
    "report_code": "11011",
    "statement_type": "consolidated"
  },
  "source_received_at": "2026-07-01T10:00:00+09:00",
  "payload": {
    "status": "000",
    "message": "정상",
    "list": [
      {"fs_div":"CFS","account_id":"ifrs-full_Revenue","account_nm":"매출액","thstrm_dt":"2025.12.31 현재","thstrm_amount":"1,234","frmtrm_amount":"1,000","currency":"KRW"},
      {"fs_div":"CFS","account_id":"dart_OperatingIncomeLoss","account_nm":"영업이익","thstrm_dt":"2025.12.31 현재","thstrm_amount":"234","frmtrm_amount":"200","currency":"KRW"},
      {"fs_div":"CFS","account_id":"ifrs-full_ProfitLoss","account_nm":"당기순이익","thstrm_dt":"2025.12.31 현재","thstrm_amount":"(45)","frmtrm_amount":"55","currency":"KRW"},
      {"fs_div":"CFS","account_id":"ifrs-full_Assets","account_nm":"자산총계","thstrm_dt":"2025.12.31 현재","thstrm_amount":"9,999","frmtrm_amount":"8,888","currency":"KRW"},
      {"fs_div":"CFS","account_id":"ifrs-full_Liabilities","account_nm":"부채총계","thstrm_dt":"2025.12.31 현재","thstrm_amount":"4,000","frmtrm_amount":"3,000","currency":"KRW"},
      {"fs_div":"CFS","account_id":"ifrs-full_Equity","account_nm":"자본총계","thstrm_dt":"2025.12.31 현재","thstrm_amount":"5,999","frmtrm_amount":"5,888","currency":"KRW"}
    ]
  }
}
EOF
.venv/bin/python scripts/build_financial_metrics.py --local-raw-input "$tmpdir/dart-wrapper.json" --validate-only
rg -n "def summarize_dart_account_mapping|def map_dart_financial_statement_rows" -n src/inno_kis_trading/data/dart.py && sed -n '580,640p' src/inno_kis_trading/data/dart.py
sed -n '699,735p' src/inno_kis_trading/data/dart.py
tmpdir=$(mktemp -d); cat > "$tmpdir/dart-wrapper.json" <<'EOF'
{
  "request": {
    "corp_code": "12345678",
    "ticker": "0A0001",
    "business_year": "2025",
    "report_code": "11011",
    "statement_type": "consolidated"
  },
  "source_received_at": "2026-07-01T10:00:00+09:00",
  "payload": {
    "status": "000",
    "message": "정상",
    "list": [
      {"fs_div":"CFS","account_id":"ifrs-full_Revenue","account_nm":"매출액","thstrm_dt":"2025.12.31 현재","thstrm_amount":"1234","frmtrm_amount":"1000","currency":"KRW"},
      {"fs_div":"CFS","account_id":"dart_OperatingIncomeLoss","account_nm":"영업이익","thstrm_dt":"2025.12.31 현재","thstrm_amount":"234","frmtrm_amount":"200","currency":"KRW"},
      {"fs_div":"CFS","account_id":"ifrs-full_ProfitLoss","account_nm":"당기순이익","thstrm_dt":"2025.12.31 현재","thstrm_amount":"45","frmtrm_amount":"55","currency":"KRW"},
      {"fs_div":"CFS","account_id":"ifrs-full_Assets","account_nm":"자산총계","thstrm_dt":"2025.12.31 현재","thstrm_amount":"9999","frmtrm_amount":"8888","currency":"KRW"},
      {"fs_div":"CFS","account_id":"ifrs-full_Liabilities","account_nm":"부채총계","thstrm_dt":"2025.12.31 현재","thstrm_amount":"4000","frmtrm_amount":"3000","currency":"KRW"},
      {"fs_div":"CFS","account_id":"ifrs-full_Equity","account_nm":"자본총계","thstrm_dt":"2025.12.31 현재","thstrm_amount":"5999","frmtrm_amount":"5888","currency":"KRW"}
    ]
  }
}
EOF
.venv/bin/python scripts/build_financial_metrics.py --local-raw-input "$tmpdir/dart-wrapper.json" --summarize-account-mapping --validate-only
git diff -- scripts/build_financial_metrics.py tests/test_build_financial_metrics.py docs/stage1-financial-input-workflow.md docs/stage1-dart-ingestion.md
git add docs/stage1-dart-ingestion.md docs/stage1-financial-input-workflow.md scripts/build_financial_metrics.py tests/test_build_financial_metrics.py && git commit -m "stage1: validate dart financial raw workflow"
.venv/bin/python scripts/build_financial_metrics.py --check-readiness --universe-input data/processed/stage1/universe_20260701.csv
git diff -- scripts/build_financial_metrics.py tests/test_build_financial_metrics.py docs/stage1-financial-input-workflow.md docs/stage1-verified-input-contracts.md
git add docs/stage1-financial-input-workflow.md docs/stage1-verified-input-contracts.md scripts/build_financial_metrics.py tests/test_build_financial_metrics.py && git commit -m "stage1: build financial input guard"
sed -n '1,360p' tests/test_build_market_input.py
rg -n "order|buy|sell|account" src/inno_kis_trading/data/kis_market.py scripts/build_market_input.py tests/test_build_market_input.py docs/stage1-market-input-workflow.md docs/stage1-kis-market-data.md
sed -n '1,240p' docs/stage1-market-input-workflow.md
sed -n '1,240p' docs/stage1-kis-market-data.md
sed -n '1,220p' docs/stage1-market-input-workflow.md
.venv/bin/python -m pytest tests/test_build_market_input.py tests/test_kis_market.py
.venv/bin/python scripts/build_market_input.py --help
.venv/bin/python scripts/build_market_input.py --check-readiness --api --universe-input data/processed/stage1/universe_20260701.csv
git diff -- scripts/build_market_input.py tests/test_build_market_input.py docs/stage1-market-input-workflow.md docs/stage1-kis-market-data.md
git add docs/stage1-kis-market-data.md docs/stage1-market-input-workflow.md scripts/build_market_input.py tests/test_build_market_input.py && git commit -m "stage1: build market input guard"
sed -n '1,320p' tests/test_pipeline.py
sed -n '1,340p' tests/test_output.py
rg -n "validate-inputs-only|readiness|metadata" tests -g '!tests/test_build_*'
sed -n '1,260p' docs/stage1-real-dry-run.md
sed -n '1,260p' docs/stage1-real-dry-run-checklist.md
sed -n '320,860p' tests/test_pipeline.py
sed -n '860,980p' tests/test_pipeline.py
.venv/bin/python -m pytest tests/test_pipeline.py tests/test_output.py
.venv/bin/python scripts/run_screener.py --validate-inputs-only --universe-input data/processed/stage1/universe_20260701.csv
git diff -- scripts/run_screener.py tests/test_pipeline.py docs/stage1-real-dry-run.md docs/stage1-real-dry-run-checklist.md
git add docs/stage1-real-dry-run-checklist.md docs/stage1-real-dry-run.md scripts/run_screener.py tests/test_pipeline.py && git commit -m "stage1: validate stage1 verified bundle"
rg -n "top_n|validation success|synthetic flag|generated output" tests/test_pipeline.py tests/test_output.py docs/stage1-real-dry-run.md docs/stage1-output.md scripts/run_screener.py src/inno_kis_trading/screener/output.py
sed -n '1,260p' docs/stage1-output.md
sed -n '1,220p' src/inno_kis_trading/screener/output.py
rg -n "source_metadata|allow_synthetic|top_n_requested" src/inno_kis_trading/screener/pipeline.py && sed -n '360,520p' src/inno_kis_trading/screener/pipeline.py
sed -n '24,120p' docs/stage1-real-dry-run.md
.venv/bin/python scripts/run_screener.py --help
.venv/bin/python scripts/run_screener.py --allow-synthetic
.venv/bin/python scripts/smoke_test.py
.venv/bin/python scripts/build_universe.py --help
git diff -- scripts/run_screener.py tests/test_pipeline.py docs/stage1-real-dry-run.md docs/stage1-real-dry-run-checklist.md docs/stage1-output.md
git add docs/stage1-output.md docs/stage1-real-dry-run-checklist.md docs/stage1-real-dry-run.md scripts/run_screener.py tests/test_pipeline.py && git commit -m "stage1: execute guarded real dry-run"
git rev-parse --short HEAD
sed -n '1,240p' /home/inno/.agents/skills/make-working-list/SKILL.md
~/.codex/bin/codex-working-list --decision 'Phase 1-29~1-35 guards were implemented fail-closed; real candidate dry-run stays blocked until verified corp mapping, financial input, and market input exist.' --todo 'Obtain verified DART corpCode ZIP/XML or official download access, then generate verified corp mapping under data/interim/' --todo 'Collect verified DART raw sample(s) and verified KIS market raw sample(s), then build financial_metrics_YYYYMMDD.csv and market_input_YYYYMMDD.csv' --next-step 'After verified financial and market inputs exist, rerun scripts/run_screener.py --validate-inputs-only and only then attempt real dry-run with explicit output paths.'
```

## 4. Tests Run

```bash
.venv/bin/python -m pytest
.venv/bin/python -m pytest tests/test_dart.py tests/test_build_dart_corp_mapping.py
.venv/bin/python -m pytest tests/test_build_dart_corp_mapping.py tests/test_dart.py
.venv/bin/python -m pytest tests/test_build_financial_metrics.py tests/test_dart.py
.venv/bin/python -m pytest tests/test_build_market_input.py tests/test_kis_market.py
.venv/bin/python -m pytest tests/test_pipeline.py tests/test_output.py
.venv/bin/python scripts/smoke_test.py
```

## 5. Decisions

- Phase 1-29~1-35 guards were implemented fail-closed; real candidate dry-run stays blocked until verified corp mapping, financial input, and market input exist.

## 6. Issues / Errors

- `.venv/bin/python -m pytest tests/test_build_dart_corp_mapping.py tests/test_dart.py` failed with exit code 1.
- `.venv/bin/python -m pytest tests/test_build_financial_metrics.py tests/test_dart.py` failed with exit code 1.
- `.venv/bin/python scripts/build_financial_metrics.py --local-raw-input /tmp/nonexistent.json --validate-only` failed with exit code 1.
- `tmpdir=$(mktemp -d); cat > "$tmpdir/dart-wrapper.json" <<'EOF' { "request": { "corp_code": "12345678", "ticker": "0A0001", "business_year": "2025", "report_code": "11011", "statement_type": "consolidated" }, "source_received_at": "2026-07-01T10:00:00+09:00", "payload": { "status": "000", "message": "정상", "list": [ {"fs_div":"CFS","account_id":"ifrs-full_Revenue","account_nm":"매출액","thstrm_dt":...
- `.venv/bin/python scripts/run_screener.py --validate-inputs-only --universe-input data/processed/stage1/universe_20260701.csv` failed with exit code 1.

## 7. TODO

- Obtain verified DART corpCode ZIP/XML or official download access, then generate verified corp mapping under data/interim/
- Collect verified DART raw sample(s) and verified KIS market raw sample(s), then build financial_metrics_YYYYMMDD.csv and market_input_YYYYMMDD.csv

## 8. Next Suggested Step

- After verified financial and market inputs exist, rerun scripts/run_screener.py --validate-inputs-only and only then attempt real dry-run with explicit output paths.

## 9. Raw Notes

- session_id: 019f1dd4-8725-7d21-b317-addde229a1cf
- session_file: /home/inno/.codex/sessions/2026/07/01/rollout-2026-07-01T22-18-15-019f1dd4-8725-7d21-b317-addde229a1cf.jsonl
- cli_version: 0.142.4
- prompt_count: 1
- first_prompt: 당신은 `inno-kis-trading` 저장소에서 Stage 1 Phase 1-29부터 Phase 1-35까지 순차적으로 수행하는 Codex 개발 에이전트다. 현재 상태: * Stage 0 완료. * Stage 1 Phase 1-1 완료. * Stage 1 Phase 1-2~1-28 완료. * 최근 완료 commit: * `8b075e9` stage1: define dart input readiness policy * `1560b79` stage1: validate dart universe...
- repo_root: /home/inno/repo/inno-kis-trading
- branch: main
- recent_commits:
- d962c61 stage1: execute guarded real dry-run
- a2b4481 stage1: validate stage1 verified bundle
- e879876 stage1: build market input guard
