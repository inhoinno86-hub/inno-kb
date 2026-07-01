from __future__ import annotations

from pathlib import Path

from inno_obsidian_ai.manifest import ManifestStore
from inno_obsidian_ai.organizer import organize_codex_logs


def test_organizer_dry_run_does_not_require_llm_or_write(config, vault: Path) -> None:
    source = vault / "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-1-1.md"
    source.write_text("Project: INNO_KIS_Trading\n\nChanged file: a.py\n", encoding="utf-8")
    manifest = ManifestStore(config.manifest_path)

    results = organize_codex_logs(config, None, manifest, dry_run=True)

    assert len(results) == 1
    assert results[0].proposal_file.endswith(".proposal.md")
    assert not any(config.review_dir.rglob("*.proposal.md"))


class _FakeClient:
    def chat_markdown(self, *, system_prompt: str, user_prompt: str) -> str:
        assert "REDACTED" in user_prompt
        return "## Summary\n\n- ok\n\n## Suggested Destination Notes\n\n- path: \"10_Projects/INNO_KIS_Trading/06_Logs/Test.md\" | reason: \"test\"\n"


def test_organizer_skips_duplicate_source_file_when_proposal_exists(config, vault: Path) -> None:
    source = vault / "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-1-1.md"
    source.write_text("Project: INNO_KIS_Trading\n\nChanged file: a.py\n", encoding="utf-8")
    existing = vault / "00_Inbox/_review/2026-06-30/working_list_2026_06_30_phase-1-1--12345678.proposal.md"
    existing.write_text(
        """---
type: llm_organization_proposal
source_file: "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-1-1.md"
source_hash: "old-hash"
project: "INNO_KIS_Trading"
feature: "phase-1-1"
status: "review"
created_at: "2026-07-01T00:00:00+09:00"
model: "test"
pipeline_run_id: "run-1"
redacted: false
---

## Summary
""",
        encoding="utf-8",
    )
    manifest = ManifestStore(config.manifest_path)

    results = organize_codex_logs(config, None, manifest, dry_run=True)

    assert len(results) == 1
    assert results[0].skipped is True
    assert results[0].reason == "existing_source_file:review"


def test_organizer_writes_pipeline_metadata_and_redaction(config, vault: Path) -> None:
    source = vault / "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-1-2.md"
    source.write_text(
        "Project: INNO_KIS_Trading\napi_key: super-secret-token-value-123456\n",
        encoding="utf-8",
    )
    manifest = ManifestStore(config.manifest_path)

    results = organize_codex_logs(
        config,
        _FakeClient(),
        manifest,
        dry_run=False,
        pipeline_run_id="run-123",
    )

    assert results[0].reason == "created"
    proposal = next(config.review_dir.rglob("*.proposal.md"))
    content = proposal.read_text(encoding="utf-8")
    assert 'source_hash: "' in content
    assert 'pipeline_run_id: "run-123"' in content
    assert "redacted: true" in content
