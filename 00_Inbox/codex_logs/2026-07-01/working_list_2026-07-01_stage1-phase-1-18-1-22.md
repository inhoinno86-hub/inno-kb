---
type: codex_session_log
source: codex
project: INNO_KIS_Trading
feature: stage1-phase-1-18-1-22
created: 2026-07-01
status: inbox
---

# Codex Working List - 2026-07-01 - stage1-phase-1-18-1-22

## 1. Goal

- Complete Stage 1 Phase 1-18 through 1-22: verified KRX universe workflow, DART financial input workflow, DART sanitized fixture coverage policy, KIS market input workflow, and real dry-run guard without fabricating real outputs.

## 2. Changed Files

| File | Change Summary |
|---|---|
| `src/inno_kis_trading/data/universe.py` | Updated via apply_patch |
| `scripts/build_universe.py` | Updated via apply_patch |
| `tests/test_build_universe.py` | Updated via apply_patch |
| `tests/test_universe.py` | Updated via apply_patch |
| `docs/stage1-krx-universe-ingestion.md` | Updated via apply_patch |
| `docs/stage1-verified-input-contracts.md` | Updated via apply_patch |
| `src/inno_kis_trading/data/dart.py` | Updated via apply_patch |
| `scripts/build_financial_metrics.py` | Added via apply_patch |
| `tests/test_dart.py` | Updated via apply_patch |
| `tests/test_build_financial_metrics.py` | Updated via apply_patch |
| `docs/stage1-financial-input-workflow.md` | Updated via apply_patch |
| `docs/stage1-dart-ingestion.md` | Updated via apply_patch |
| `docs/stage1-dart-account-mapping.md` | Updated via apply_patch |
| `scripts/build_market_input.py` | Added via apply_patch |
| `tests/test_build_market_input.py` | Added via apply_patch |
| `docs/stage1-market-input-workflow.md` | Added via apply_patch |
| `docs/stage1-kis-market-data.md` | Updated via apply_patch |
| `scripts/run_screener.py` | Updated via apply_patch |
| `tests/test_pipeline.py` | Updated via apply_patch |
| `docs/stage1-real-dry-run.md` | Updated via apply_patch |
| `docs/stage1-real-dry-run-checklist.md` | Updated via apply_patch |

## 3. Commands Run

```bash
pwd
git status --short
git log --oneline -15
find . -maxdepth 4 -type f | sort | sed 's#^\./##' | head -350
git ls-files data/raw data/interim data/processed reports
git status --short --ignored data/raw data/interim data/processed reports | head -100
cat ~/.codex/AGENTS.md
.venv/bin/python -m pytest
sed -n '1,260p' scripts/build_universe.py
sed -n '1,260p' src/inno_kis_trading/data/universe.py
sed -n '1,320p' src/inno_kis_trading/screener/input_contracts.py
sed -n '1,260p' docs/stage1-krx-universe-ingestion.md
sed -n '1,260p' docs/stage1-verified-input-contracts.md
sed -n '1,220p' data/README.md
sed -n '1,220p' .gitignore
sed -n '1,260p' tests/test_build_universe.py
sed -n '261,520p' scripts/build_universe.py
sed -n '261,520p' src/inno_kis_trading/data/universe.py
sed -n '261,520p' tests/test_build_universe.py
sed -n '1,260p' tests/test_universe.py
rg -n "validate_universe_input_contract|verification_status|source_id|source_url|source metadata|allow-write" -n scripts/build_universe.py src/inno_kis_trading/data/universe.py tests/test_build_universe.py tests/test_universe.py docs/stage1-krx-universe-ingestion.md docs/stage1-verified-input-contracts.md
.venv/bin/python scripts/build_universe.py --help
sed -n '1,260p' src/inno_kis_trading/config.py
sed -n '1,220p' config/config.example.yaml
mktemp
tmp_config=$(mktemp)
cat > "$tmp_config" <<'EOF'
data:
  allow_external_download: true
  universe_provider: "KRX"
EOF
.venv/bin/python scripts/build_universe.py --download --validate-only --config "$tmp_config"
status=$?
rm -f "$tmp_config"
exit $status
python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('src').resolve()))
import requests
from inno_kis_trading.data.universe import KIND_CORP_LIST_URL, _read_kind_response_text, _parse_kind_corp_list_html
r = requests.get(KIND_CORP_LIST_URL, timeout=30)
print('status', r.status_code)
print('content-type', r.headers.get('content-type'))
text = _read_kind_response_text(r, endpoint_label='corp list download')
rows = _parse_kind_corp_list_html(text)
print('rows', len(rows))
for row in rows[:10]:
    print(row['종목코드'], row['회사명'], row['시장구분'])
PY
python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('src').resolve()))
import requests
from inno_kis_trading.data.universe import KIND_LISTED_ISSUE_STATUS_DETAIL_URL, _read_kind_response_text, _parse_kind_company_basis_issue_html
for market_id in ('STK','KSQ'):
    r = requests.post(KIND_LISTED_ISSUE_STATUS_DETAIL_URL, data={
        'method':'searchListedIssueStatDetailSub',
        'forward':'listedissuestatdetail_down',
        'selDate':'20260701',
        'mktId':market_id,
        'secugrpId':'ST',
        'detailType':'1',
        'currentPageSize':'5000',
        'pageIndex':'1',
    }, timeout=30)
    print('market', market_id, 'status', r.status_code, 'content-type', r.headers.get('content-type'))
    text = _read_kind_response_text(r, endpoint_label=f'listed issue {market_id}')
    rows = _parse_kind_company_basis_issue_html(text)
    print('rows', len(rows))
    for row in rows[:5]:
        print(row['종목코드'], row['회사명'], row['시장구분'], row['구분'])
PY
.venv/bin/python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('src').resolve()))
import requests
from inno_kis_trading.data.universe import KIND_CORP_LIST_URL, _read_kind_response_text, _parse_kind_corp_list_html
r = requests.get(KIND_CORP_LIST_URL, timeout=30)
print('status', r.status_code)
print('content-type', r.headers.get('content-type'))
text = _read_kind_response_text(r, endpoint_label='corp list download')
rows = _parse_kind_corp_list_html(text)
print('rows', len(rows))
for row in rows[:10]:
    print(row['종목코드'], row['회사명'], row['시장구분'])
PY
.venv/bin/python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('src').resolve()))
import requests
from inno_kis_trading.data.universe import KIND_LISTED_ISSUE_STATUS_DETAIL_URL, _read_kind_response_text, _parse_kind_company_basis_issue_html
for market_id in ('STK','KSQ'):
    r = requests.post(KIND_LISTED_ISSUE_STATUS_DETAIL_URL, data={
        'method':'searchListedIssueStatDetailSub',
        'forward':'listedissuestatdetail_down',
        'selDate':'20260701',
        'mktId':market_id,
        'secugrpId':'ST',
        'detailType':'1',
        'currentPageSize':'5000',
        'pageIndex':'1',
    }, timeout=30)
    print('market', market_id, 'status', r.status_code, 'content-type', r.headers.get('content-type'))
    text = _read_kind_response_text(r, endpoint_label=f'listed issue {market_id}')
    rows = _parse_kind_company_basis_issue_html(text)
    print('rows', len(rows))
    for row in rows[:5]:
        print(row['종목코드'], row['회사명'], row['시장구분'], row['구분'])
PY
.venv/bin/python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('src').resolve()))
import requests
from collections import Counter
from inno_kis_trading.data.universe import KIND_CORP_LIST_URL, _read_kind_response_text, _parse_kind_corp_list_html, _map_kind_market, _normalize_provider_ticker
r = requests.get(KIND_CORP_LIST_URL, timeout=30)
text = _read_kind_response_text(r, endpoint_label='corp list download')
rows = _parse_kind_corp_list_html(text)
filtered = []
for row in rows:
    if _map_kind_market(row['시장구분']) is None:
        continue
    filtered.append((_normalize_provider_ticker(row['종목코드']), row['회사명'], row['시장구분']))
counts = Counter(t for t,_,_ in filtered)
dups = [t for t,c in counts.items() if c > 1]
print('dup_count', len(dups))
for t in dups[:20]:
    print('dup', t)
    for row in filtered:
        if row[0] == t:
            print('  ', row)
PY
rg -n "def _normalize_source_reference|source_id|source_url|validate_universe_input_contract" src/inno_kis_trading/screener/input_contracts.py
sed -n '260,520p' src/inno_kis_trading/screener/input_contracts.py
sed -n '1,240p' tests/test_input_contracts.py
.venv/bin/python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('src').resolve()))
import requests
from collections import Counter
from inno_kis_trading.data.universe import KIND_LISTED_ISSUE_STATUS_DETAIL_URL, _read_kind_response_text, _parse_kind_company_basis_issue_html, _normalize_provider_ticker
for market_id in ('STK','KSQ'):
    r = requests.post(KIND_LISTED_ISSUE_STATUS_DETAIL_URL, data={
        'method':'searchListedIssueStatDetailSub',
        'forward':'listedissuestatdetail_down',
        'selDate':'20260701',
        'mktId':market_id,
        'secugrpId':'ST',
        'detailType':'1',
        'currentPageSize':'5000',
        'pageIndex':'1',
    }, timeout=30)
    text = _read_kind_response_text(r, endpoint_label=f'listed issue {market_id}')
    rows = _parse_kind_company_basis_issue_html(text)
    vals = [(_normalize_provider_ticker(row['종목코드']), row['회사명'], row['시장구분'], row['구분']) for row in rows]
    counts = Counter(t for t, *_ in vals)
    dups = [t for t,c in counts.items() if c > 1]
    print(market_id, 'dup_count', len(dups))
    if dups:
        for t in dups[:10]:
            print('dup', t)
            for row in vals:
                if row[0] == t:
                    print(' ', row)
PY
rg -n "Duplicate ticker found in KIND corp list|Duplicate ticker found in KIND listed issue company-basis rows|corp list" tests/test_universe.py
sed -n '240,420p' tests/test_universe.py
sed -n '420,680p' tests/test_universe.py
sed -n '1,220p' scripts/build_universe.py
sed -n '220,380p' scripts/build_universe.py
sed -n '380,460p' scripts/build_universe.py
.venv/bin/python -m pytest tests/test_build_universe.py tests/test_universe.py tests/test_input_contracts.py
.venv/bin/python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('src').resolve()))
import requests
from inno_kis_trading.data.universe import KIND_CORP_LIST_URL, _read_kind_response_text, _parse_kind_corp_list_html
r = requests.get(KIND_CORP_LIST_URL, timeout=30)
rows = _parse_kind_corp_list_html(_read_kind_response_text(r, endpoint_label='corp list download'))
for ticker in ('0001A0','439260'):
    matches = [row for row in rows if row['종목코드'].strip().upper() == ticker]
    print('ticker', ticker, 'count', len(matches))
    for row in matches:
        print(row)
PY
tmp_config=$(mktemp)
cat > "$tmp_config" <<'EOF'
data:
  allow_external_download: true
  universe_provider: "KRX"
EOF
.venv/bin/python scripts/build_universe.py --download --config "$tmp_config" --output data/processed/stage1/universe_20260701.csv --allow-write
status=$?
rm -f "$tmp_config"
exit $status
git status --short --ignored data/processed/stage1 | head -50
ls -l data/processed/stage1/universe_20260701.csv data/processed/stage1/universe_20260701.metadata.json
git status --short --ignored data/processed/stage1 data/processed | head -50
git diff -- AGENTS.md
git diff -- scripts/build_universe.py src/inno_kis_trading/data/universe.py
git diff -- tests/test_build_universe.py tests/test_universe.py
git diff -- docs/stage1-krx-universe-ingestion.md docs/stage1-verified-input-contracts.md
.venv/bin/python -m pytest tests/test_universe.py tests/test_build_universe.py
git diff -- docs/stage1-krx-universe-ingestion.md tests/test_universe.py
git add docs/stage1-krx-universe-ingestion.md docs/stage1-verified-input-contracts.md scripts/build_universe.py src/inno_kis_trading/data/universe.py tests/test_build_universe.py tests/test_universe.py && git commit -m "stage1: validate krx universe input workflow"
sed -n '1,320p' src/inno_kis_trading/data/dart.py
sed -n '1,260p' docs/stage1-dart-ingestion.md
sed -n '1,320p' docs/stage1-dart-account-mapping.md
sed -n '1,260p' src/inno_kis_trading/screener/metrics.py
sed -n '1,320p' tests/test_dart.py
rg -n "financial|dart|build_financial|account mapping|sanitized" scripts src docs tests
sed -n '84,220p' src/inno_kis_trading/screener/pipeline.py
sed -n '220,340p' src/inno_kis_trading/screener/pipeline.py
sed -n '1,220p' scripts/run_screener.py
find tests/fixtures -maxdepth 3 -type f | sort
sed -n '320,460p' src/inno_kis_trading/data/dart.py
rg -n "corp_code|corp mapping|universe-input|source_received_date|financial input workflow" src tests docs scripts
find docs -maxdepth 2 -type f | sort | rg 'financial|dart|dry-run|market'
sed -n '1,320p' src/inno_kis_trading/data/kis_market.py
sed -n '1,320p' tests/test_kis_market.py
.venv/bin/python -m pytest tests/test_dart.py tests/test_build_financial_metrics.py tests/test_input_contracts.py
.venv/bin/python scripts/build_financial_metrics.py --help
.venv/bin/python scripts/build_financial_metrics.py --local-raw-input /tmp/does-not-exist.json --validate-only
tmp_json=$(mktemp)
cat > "$tmp_json" <<'EOF'
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
    "message": "ok",
    "list": [
      {"fs_div": "CFS", "account_id": "ifrs-full_Revenue", "account_nm": "매출액", "thstrm_dt": "2025.12.31 현재", "thstrm_amount": "1,234", "frmtrm_amount": "1,000", "currency": "KRW"},
      {"fs_div": "CFS", "account_id": "dart_OperatingIncomeLoss", "account_nm": "영업이익", "thstrm_dt": "2025.12.31 현재", "thstrm_amount": "234", "frmtrm_amount": "200", "currency": "KRW"},
      {"fs_div": "CFS", "account_id": "ifrs-full_ProfitLoss", "account_nm": "당기순이익", "thstrm_dt": "2025.12.31 현재", "thstrm_amount": "(45)", "frmtrm_amount": "55", "currency": "KRW"},
      {"fs_div": "CFS", "account_id": "ifrs-full_Assets", "account_nm": "자산총계", "thstrm_dt": "2025.12.31 현재", "thstrm_amount": "9,999", "frmtrm_amount": "8,888", "currency": "KRW"},
      {"fs_div": "CFS", "account_id": "ifrs-full_Liabilities", "account_nm": "부채총계", "thstrm_dt": "2025.12.31 현재", "thstrm_amount": "4,000", "frmtrm_amount": "3,000", "currency": "KRW"},
      {"fs_div": "CFS", "account_id": "ifrs-full_Equity", "account_nm": "자본총계", "thstrm_dt": "2025.12.31 현재", "thstrm_amount": "5,999", "frmtrm_amount": "5,888", "currency": "KRW"}
    ]
  }
}
EOF
.venv/bin/python scripts/build_financial_metrics.py --local-raw-input "$tmp_json" --validate-only
status=$?
rm -f "$tmp_json"
exit $status
git diff -- src/inno_kis_trading/data/dart.py scripts/build_financial_metrics.py
git diff -- tests/test_dart.py tests/test_build_financial_metrics.py
git diff -- docs/stage1-dart-ingestion.md docs/stage1-financial-input-workflow.md docs/stage1-verified-input-contracts.md
sed -n '1,320p' scripts/build_financial_metrics.py
sed -n '1,260p' docs/stage1-financial-input-workflow.md
sed -n '1,260p' tests/test_build_financial_metrics.py
git add docs/stage1-dart-ingestion.md docs/stage1-financial-input-workflow.md docs/stage1-verified-input-contracts.md scripts/build_financial_metrics.py src/inno_kis_trading/data/dart.py tests/test_dart.py tests/test_build_financial_metrics.py && git commit -m "stage1: add dart financial input workflow"
find tests -maxdepth 4 -type f | sort | rg 'dart|fixture|json|yaml'
find data/raw data/interim data/processed -maxdepth 4 -type f | sort | head -200
git ls-files data/raw data/interim data/processed | sort
git status --short --ignored data/raw data/interim data/processed | head -100
sed -n '1,260p' docs/stage1-dart-account-mapping.md
.venv/bin/python -m pytest tests/test_dart.py tests/test_build_financial_metrics.py
git diff -- src/inno_kis_trading/data/dart.py docs/stage1-dart-account-mapping.md docs/stage1-financial-input-workflow.md tests/test_dart.py
git add docs/stage1-dart-account-mapping.md docs/stage1-financial-input-workflow.md src/inno_kis_trading/data/dart.py tests/test_dart.py && git commit -m "stage1: document dart sanitized fixture coverage"
sed -n '1,260p' docs/stage1-kis-market-data.md
rg -n "build_market|market input workflow|KIS market|order endpoint|place_order" scripts docs src tests
.venv/bin/python -m pytest tests/test_kis_market.py tests/test_build_market_input.py tests/test_input_contracts.py
.venv/bin/python scripts/build_market_input.py --help
git diff -- docs/stage1-kis-market-data.md docs/stage1-market-input-workflow.md docs/stage1-verified-input-contracts.md
sed -n '1,260p' scripts/build_market_input.py
sed -n '1,260p' tests/test_build_market_input.py
git add docs/stage1-kis-market-data.md docs/stage1-market-input-workflow.md docs/stage1-verified-input-contracts.md scripts/build_market_input.py tests/test_build_market_input.py && git commit -m "stage1: add kis market input workflow"
sed -n '1,260p' docs/stage1-real-dry-run.md
sed -n '1,260p' docs/stage1-real-dry-run-checklist.md
sed -n '1,260p' tests/test_pipeline.py
sed -n '260,520p' tests/test_pipeline.py
find data/processed/stage1 data/interim -maxdepth 3 -type f | sort
sed -n '1,240p' src/inno_kis_trading/screener/output.py
rg -n "validate-inputs-only|joined_rows|verification_status|report_path|output_csv|allow-synthetic|Missing.*input|Verified inputs" scripts/run_screener.py tests/test_pipeline.py docs/stage1-real-dry-run.md docs/stage1-real-dry-run-checklist.md
.venv/bin/python -m pytest tests/test_pipeline.py tests/test_output.py
git diff -- scripts/run_screener.py tests/test_pipeline.py docs/stage1-real-dry-run.md docs/stage1-real-dry-run-checklist.md
.venv/bin/python scripts/smoke_test.py
.venv/bin/python scripts/run_screener.py --help
.venv/bin/python scripts/run_screener.py --allow-synthetic
git add docs/stage1-real-dry-run-checklist.md docs/stage1-real-dry-run.md scripts/run_screener.py tests/test_pipeline.py && git commit -m "stage1: add stage1 real dry-run execution guard"
git log --oneline -8
~/.codex/bin/codex-working-list --help
date +%F
git branch --show-current
~/.codex/bin/codex-working-list --repo /home/inno/repo/inno-kis-trading --project INNO_KIS_Trading --feature-name stage1-phase-1-18-1-22 --goal 'Complete Stage 1 Phase 1-18 through 1-22: verified KRX universe workflow, DART financial input workflow, DART sanitized fixture coverage policy, KIS market input workflow, and real dry-run guard without fabricating real outputs.' --decision 'KRX/KIND corp-list rows with the same ticker/company_name/market are deduplicated, while conflicting duplicates still fail closed.' --decision 'DART financial input and KIS market input are generated only through explicit CLI workflows that validate Stage 1 verified input contracts before reporting success.' --decision 'Real dry-run remains blocked unless verified universe, financial, and market input files all exist and pass verification_status=verified.' --todo 'Collect or generate one verified DART financial input file from reviewed local raw data or credentials-backed API access.' --todo 'Collect or generate one verified KIS market input file from reviewed local raw data or credentials-backed API access.' --todo 'Run scripts/run_screener.py --validate-inputs-only with the three verified inputs before any real dry-run.' --next-step 'Prepare verified DART and KIS local inputs, then run the real dry-run readiness command and only execute the dry-run if all three verified inputs pass validation.' --raw-note 'Commits created in this session: 1541850, ca6b974, 1fb9b3f, 1d91b4d, 3925e5e.'
```

## 4. Tests Run

```bash
.venv/bin/python -m pytest
.venv/bin/python -m pytest tests/test_build_universe.py tests/test_universe.py tests/test_input_contracts.py
.venv/bin/python -m pytest tests/test_universe.py tests/test_build_universe.py
.venv/bin/python -m pytest tests/test_dart.py tests/test_build_financial_metrics.py tests/test_input_contracts.py
.venv/bin/python -m pytest tests/test_dart.py tests/test_build_financial_metrics.py
.venv/bin/python -m pytest tests/test_kis_market.py tests/test_build_market_input.py tests/test_input_contracts.py
.venv/bin/python -m pytest tests/test_pipeline.py tests/test_output.py
.venv/bin/python scripts/smoke_test.py
```

## 5. Decisions

- KRX/KIND corp-list rows with the same ticker/company_name/market are deduplicated, while conflicting duplicates still fail closed.
- DART financial input and KIS market input are generated only through explicit CLI workflows that validate Stage 1 verified input contracts before reporting success.
- Real dry-run remains blocked unless verified universe, financial, and market input files all exist and pass verification_status=verified.

## 6. Issues / Errors

- `tmp_config=$(mktemp) cat > "$tmp_config" <<'EOF' data: allow_external_download: true universe_provider: "KRX" EOF .venv/bin/python scripts/build_universe.py --download --validate-only --config "$tmp_config" status=$? rm -f "$tmp_config" exit $status` failed with exit code 1.
- `python - <<'PY' from pathlib import Path import sys sys.path.insert(0, str(Path('src').resolve())) import requests from inno_kis_trading.data.universe import KIND_CORP_LIST_URL, _read_kind_response_text, _parse_kind_corp_list_html r = requests.get(KIND_CORP_LIST_URL, timeout=30) print('status', r.status_code) print('content-type', r.headers.get('content-type')) text = _read_kind_response_text(...
- `python - <<'PY' from pathlib import Path import sys sys.path.insert(0, str(Path('src').resolve())) import requests from inno_kis_trading.data.universe import KIND_LISTED_ISSUE_STATUS_DETAIL_URL, _read_kind_response_text, _parse_kind_company_basis_issue_html for market_id in ('STK','KSQ'): r = requests.post(KIND_LISTED_ISSUE_STATUS_DETAIL_URL, data={ 'method':'searchListedIssueStatDetailSub', '...
- `.venv/bin/python -m pytest tests/test_build_universe.py tests/test_universe.py tests/test_input_contracts.py` failed with exit code 1.
- `.venv/bin/python -m pytest tests/test_dart.py tests/test_build_financial_metrics.py tests/test_input_contracts.py` failed with exit code 1.
- `.venv/bin/python scripts/build_financial_metrics.py --local-raw-input /tmp/does-not-exist.json --validate-only` failed with exit code 1.

## 7. TODO

- Collect or generate one verified DART financial input file from reviewed local raw data or credentials-backed API access.
- Collect or generate one verified KIS market input file from reviewed local raw data or credentials-backed API access.
- Run scripts/run_screener.py --validate-inputs-only with the three verified inputs before any real dry-run.

## 8. Next Suggested Step

- Prepare verified DART and KIS local inputs, then run the real dry-run readiness command and only execute the dry-run if all three verified inputs pass validation.

## 9. Raw Notes

- session_id: 019f1c7b-2c40-7de2-a989-55a0e446dce0
- session_file: /home/inno/.codex/sessions/2026/07/01/rollout-2026-07-01T16-01-02-019f1c7b-2c40-7de2-a989-55a0e446dce0.jsonl
- cli_version: 0.142.4
- prompt_count: 2
- first_prompt: superpowers 사용 안함 당신은 `inno-kis-trading` 저장소에서 Stage 1 Phase 1-18부터 Phase 1-22까지 순차적으로 수행하는 Codex 개발 에이전트다. 현재 상태: * Stage 0 완료. * Stage 1 Phase 1-1 완료. * Stage 1 Phase 1-2~1-17 완료. * 최근 완료 commit: * `e2e1e74` stage1: define verified input schema contracts * `9eaa23f` stage1:...
- repo_root: /home/inno/repo/inno-kis-trading
- branch: main
- recent_commits:
- 3925e5e stage1: add stage1 real dry-run execution guard
- 1d91b4d stage1: add kis market input workflow
- 1fb9b3f stage1: document dart sanitized fixture coverage
- Commits created in this session: 1541850, ca6b974, 1fb9b3f, 1d91b4d, 3925e5e.
