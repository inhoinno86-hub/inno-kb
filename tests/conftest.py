from __future__ import annotations

from pathlib import Path

import pytest

from inno_obsidian_ai.config import AppConfig, load_config


def write_config(vault_path: Path) -> Path:
    config_path = vault_path / "config.yaml"
    config_path.write_text(
        f"""
vault_path: "{vault_path.as_posix()}"
inbox:
  codex_logs: "00_Inbox/codex_logs"
  review: "00_Inbox/_review"
  processed: "00_Inbox/_processed"
nvidia:
  base_url: "https://integrate.api.nvidia.com/v1"
  llm_model: "test-llm"
  embedding_model: "test-embed"
  rerank_model: ""
  timeout_seconds: 60
rag:
  vector_db: "chroma"
  persist_dir: ".inno_rag/chroma"
  chunk_size: 200
  chunk_overlap: 40
  top_k: 4
  rerank_top_k: 2
  index_raw_codex_logs: false
  collection_name: "test-vault"
safety:
  dry_run: true
  require_approval_for_apply: true
  append_only: true
  redact_secrets: true
""".strip(),
        encoding="utf-8",
    )
    return config_path


@pytest.fixture()
def vault(tmp_path: Path) -> Path:
    for relative in [
        "00_Inbox/codex_logs/2026-06-30",
        "00_Inbox/_review/2026-06-30",
        "00_Inbox/_processed",
        "10_Projects/INNO_KIS_Trading/06_Logs",
    ]:
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)
    return tmp_path


@pytest.fixture()
def config(vault: Path) -> AppConfig:
    config_path = write_config(vault)
    return load_config(config_path)
