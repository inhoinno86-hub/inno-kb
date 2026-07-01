from __future__ import annotations

from pathlib import Path

import pytest

from inno_obsidian_ai.config import ConfigError, ensure_within


def test_path_confinement_accepts_child(vault: Path) -> None:
    child = vault / "00_Inbox" / "codex.md"
    assert ensure_within(vault, child) == child.resolve()


def test_path_confinement_rejects_escape(vault: Path) -> None:
    with pytest.raises(ConfigError):
        ensure_within(vault, vault / ".." / "outside.md")
