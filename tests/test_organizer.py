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
