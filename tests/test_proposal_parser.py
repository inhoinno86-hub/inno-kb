from __future__ import annotations

from pathlib import Path

import pytest

from inno_obsidian_ai.config import ConfigError
from inno_obsidian_ai.proposal_parser import load_proposal


def test_rejects_source_file_outside_vault(config, vault: Path) -> None:
    proposal = vault / "00_Inbox/_review/2026-06-30/test.proposal.md"
    proposal.write_text(
        """---
type: llm_organization_proposal
source_file: "../outside.md"
project: "INNO_KIS_Trading"
feature: "phase-1-1"
status: "approved"
created_at: "2026-06-30T00:00:00+09:00"
model: "test"
source_hash: "hash"
---

# Organization Proposal

## Suggested Destination Notes

- path: "10_Projects/INNO_KIS_Trading/06_Logs/Daily Dev Log.md" | reason: "test"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError):
        load_proposal(config, proposal)
