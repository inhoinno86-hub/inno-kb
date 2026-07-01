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


def test_config_defaults_exclude_raw_logs_and_maps_collections(config) -> None:
    assert "00_Inbox/codex_logs/**/*.md" in config.indexing.exclude_patterns
    assert config.indexing.policy_for("decision", config.rag.collection_name).collection == "decisions"
    assert config.automation.allow_full_vault_index is False
    assert config.operation_log.destination.endswith("Obsidian AI Pipeline Log.md")
    assert config.dashboard.auto_section_start == "<!-- BEGIN_AUTO_OBSIDIAN_AI_DASHBOARD -->"
