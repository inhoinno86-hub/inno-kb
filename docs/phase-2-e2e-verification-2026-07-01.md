# Phase 2 E2E Verification 2026-07-01

## Scope

- Verified Phase 2 pipeline behavior without modifying Phase 1 hook work.
- Used sample source log `00_Inbox/codex_logs/2026-07-01/working_list_2026_07_01_phase-2-e2e-verification-sample.md`.

## Verified

- `organize_codex_inbox_with_nvidia.py` dry-run scanned the sample source and produced the expected proposal path.
- `organize_codex_inbox_with_nvidia.py --write` succeeded with live NVIDIA hosted NIM and created a proposal in `00_Inbox/_review_live_e2e/2026-07-01/`.
- Generated proposal frontmatter included `type`, `source_file`, `project`, `feature`, `status`, `created_at`, `model`, and `source_hash`.
- Approved proposal append wrote to `10_Projects/INNO_KIS_Trading/06_Logs/Phase 2 Live E2E Verification Sandbox.md`.
- Re-running apply did not append twice.
- `review` and `rejected` proposals were skipped.
- Source log SHA-256 stayed unchanged before and after verification.
- Live Chroma persistent files were created under `.inno_rag/chroma_live_e2e_subset/`.
- `index_obsidian_vault.py --write --path-prefix ...` succeeded with live NVIDIA embeddings and Chroma persistence.
- `ask_vault.py` succeeded in a new process with live NVIDIA query embedding + completion and returned a `Sources` section.
- `ask_vault.py` returned `근거 부족` with `Sources: - none` for an unrelated live query against the subset collection.
- `ask_vault.py` missing-key path was previously verified to fail clearly.
- `ask_vault.py` `근거 부족` output format was previously smoke-tested with fake client/store.

## Fixes Found During Verification

- `index_obsidian_vault.py` originally crashed on invalid YAML frontmatter in existing vault templates.
- `markdown_loader.parse_frontmatter()` now falls back to empty frontmatter when YAML parse fails.
- `redact_secrets()` originally redacted long snake_case command names such as `organize_codex_inbox_with_nvidia.py`.
- Redaction heuristic now preserves long identifiers while still masking likely secret tokens.
- NVIDIA embedding requests for `nvidia/nv-embedqa-e5-v5` needed `input_type`.
- NVIDIA embedding client now sends `input_type`, batches defensively, and retries transient 5xx responses.
- `index_obsidian_vault.py` now excludes all `00_Inbox/codex_logs`, `_review*`, and `_processed*` paths by default, and supports `--path-prefix` for targeted indexing.

## Constraints Observed

- Full-vault live indexing through NVIDIA embeddings was functional but slow enough that targeted validation was more practical for this session.
- A partial full-vault live indexing attempt wrote real Chroma/manifest state before being stopped in favor of the targeted `--path-prefix` validation path.
- The chosen embedding model enforced a 512-token input cap in practice, so the safe default `rag.chunk_size` was reduced to `500`.

## Evidence

- Source hash: `876fac6d59b3c8510f8130be45ff3d75e5dd8c5d4759c4d9b419a0eef023482a`
- Live append target hash after idempotency check: `72c6163ac2f1f3f9d3c45166dc48c6bc427bcec848557940278671109251a9a0`
- Manifest path: `.inno_rag/manifest.sqlite`
- Live Chroma subset path: `.inno_rag/chroma_live_e2e_subset/`
