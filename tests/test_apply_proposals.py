from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "apply_approved_proposals.py"


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
