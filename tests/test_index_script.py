from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "index_obsidian_vault.py"
SPEC = importlib.util.spec_from_file_location("index_obsidian_vault_script", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_should_index_excludes_raw_logs_and_review(config) -> None:
    assert MODULE.should_index(config, "00_Inbox/codex_logs/2026-07-01/a.md") is False
    assert MODULE.should_index(config, "00_Inbox/_review/2026-07-01/a.md") is False
    assert MODULE.should_index(config, "10_Projects/INNO_KIS_Trading/06_Logs/a.md") is True


def test_should_index_honors_path_prefix(config) -> None:
    assert (
        MODULE.should_index(
            config,
            "10_Projects/INNO_KIS_Trading/06_Logs/a.md",
            ["10_Projects/INNO_KIS_Trading/06_Logs"],
        )
        is True
    )
    assert (
        MODULE.should_index(
            config,
            "10_Projects/INNO_KIS_Trading/07_References/b.md",
            ["10_Projects/INNO_KIS_Trading/06_Logs"],
        )
        is False
    )
