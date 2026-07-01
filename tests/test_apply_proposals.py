from __future__ import annotations

import subprocess
import sys
import importlib.util
from pathlib import Path

from inno_obsidian_ai.audit import AuditLogger
from inno_obsidian_ai.manifest import ManifestStore


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "apply_approved_proposals.py"
SPEC = importlib.util.spec_from_file_location("apply_approved_proposals_script", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_proposal(vault: Path, *, status: str, target: str, name: str = "proposal.md") -> Path:
    proposal = vault / "00_Inbox/_review/2026-06-30" / name
    proposal.write_text(
        f"""---
type: llm_organization_proposal
source_file: "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-1-1.md"
project: "INNO_KIS_Trading"
feature: "phase-1-1"
status: "{status}"
created_at: "2026-06-30T00:00:00+09:00"
model: "test"
source_hash: "hash"
---

# Organization Proposal

## Summary

- test summary

## Changed Files

- a.py

## Commands

- pytest

## Tests

- passed

## Decisions

- keep append only

## TODO

- none

## Risks / Follow-up

- review

## Suggested Destination Notes

- path: "{target}" | reason: "apply test"

## Suggested Obsidian Links

- [[INNO_KIS_Trading]]

## Uncertain Items

- 확인 필요

## Human Review Required

- verify path
""",
        encoding="utf-8",
    )
    return proposal


def test_only_approved_status_is_applied(config, vault: Path) -> None:
    source = vault / "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-1-1.md"
    source.write_text("source", encoding="utf-8")
    target = "10_Projects/INNO_KIS_Trading/06_Logs/Daily Dev Log.md"
    write_proposal(vault, status="review", target=target)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(config.config_path), "--write"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert not (vault / target).exists()


def test_append_only_application_preserves_existing_content(config, vault: Path) -> None:
    source = vault / "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-1-1.md"
    source.write_text("source", encoding="utf-8")
    target = vault / "10_Projects/INNO_KIS_Trading/06_Logs/Daily Dev Log.md"
    target.write_text("# Existing\n\nOld content\n", encoding="utf-8")
    write_proposal(
        vault,
        status="approved",
        target="10_Projects/INNO_KIS_Trading/06_Logs/Daily Dev Log.md",
        name="approved.proposal.md",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--config", str(config.config_path), "--write"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    updated = target.read_text(encoding="utf-8")
    assert updated.startswith("# Existing")
    assert "Old content" in updated
    assert "## 2026-06-30 - phase-1-1" in updated
    assert "keep append only" in updated


def test_apply_returns_changed_notes_and_marks_applied(config, vault: Path) -> None:
    source = vault / "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-1-2.md"
    source.write_text("source", encoding="utf-8")
    proposal = write_proposal(
        vault,
        status="approved",
        target="10_Projects/INNO_KIS_Trading/06_Logs/Daily Dev Log.md",
        name="approved-2.proposal.md",
    )
    manifest = ManifestStore(config.manifest_path)
    audit = AuditLogger(config.audit_log_dir)

    results = MODULE.apply_approved_proposals(
        config,
        manifest,
        dry_run=False,
        pipeline_run_id="run-apply",
        audit_logger=audit,
    )

    assert results[0].changed_notes == ("10_Projects/INNO_KIS_Trading/06_Logs/Daily Dev Log.md",)
    updated = proposal.read_text(encoding="utf-8")
    assert 'status: applied' in updated
    assert 'applied_run_id: run-apply' in updated


def test_applied_proposal_is_not_appended_twice(config, vault: Path) -> None:
    source = vault / "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-1-3.md"
    source.write_text("source", encoding="utf-8")
    write_proposal(
        vault,
        status="approved",
        target="10_Projects/INNO_KIS_Trading/06_Logs/Daily Dev Log.md",
        name="approved-3.proposal.md",
    )
    manifest = ManifestStore(config.manifest_path)

    first = MODULE.apply_approved_proposals(config, manifest, dry_run=False, pipeline_run_id="run-1")
    second = MODULE.apply_approved_proposals(config, manifest, dry_run=False, pipeline_run_id="run-2")

    target = vault / "10_Projects/INNO_KIS_Trading/06_Logs/Daily Dev Log.md"
    content = target.read_text(encoding="utf-8")
    assert content.count("## 2026-06-30 - phase-1-1") == 1
    assert first[0].changed_notes == ("10_Projects/INNO_KIS_Trading/06_Logs/Daily Dev Log.md",)
    assert second[0].skipped is True
