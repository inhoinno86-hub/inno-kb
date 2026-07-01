from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    pass


def ensure_within(base: Path, candidate: Path) -> Path:
    base_resolved = base.expanduser().resolve()
    candidate_resolved = candidate.expanduser().resolve()

    try:
        candidate_resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ConfigError(
            f"Path escapes vault confinement: {candidate_resolved} (base: {base_resolved})"
        ) from exc

    return candidate_resolved


def _require_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"Expected mapping for '{field_name}'")
    return value


def _require_str(mapping: dict[str, Any], key: str, field_name: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"Missing required string '{field_name}.{key}'")
    return value.strip()


def _require_int(mapping: dict[str, Any], key: str, field_name: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int):
        raise ConfigError(f"Missing required integer '{field_name}.{key}'")
    return value


def _require_bool(mapping: dict[str, Any], key: str, field_name: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ConfigError(f"Missing required boolean '{field_name}.{key}'")
    return value


@dataclass(frozen=True)
class InboxConfig:
    codex_logs: str
    review: str
    processed: str


@dataclass(frozen=True)
class NvidiaConfig:
    base_url: str
    llm_model: str
    embedding_model: str
    rerank_model: str
    timeout_seconds: int = 60


@dataclass(frozen=True)
class RagConfig:
    vector_db: str
    persist_dir: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    rerank_top_k: int
    index_raw_codex_logs: bool = False
    collection_name: str = "inno_obsidian_vault"


@dataclass(frozen=True)
class SafetyConfig:
    dry_run: bool
    require_approval_for_apply: bool
    append_only: bool
    redact_secrets: bool


@dataclass(frozen=True)
class AppConfig:
    vault_path: Path
    inbox: InboxConfig
    nvidia: NvidiaConfig
    rag: RagConfig
    safety: SafetyConfig
    config_path: Path

    def resolve_in_vault(self, relative_path: str | Path) -> Path:
        return ensure_within(self.vault_path, self.vault_path / Path(relative_path))

    def resolve_data_path(self, relative_path: str | Path) -> Path:
        return ensure_within(self.vault_path, self.vault_path / Path(relative_path))

    def to_vault_relative(self, path: Path) -> str:
        confined = ensure_within(self.vault_path, path)
        return confined.relative_to(self.vault_path).as_posix()

    @property
    def manifest_path(self) -> Path:
        return self.resolve_data_path(".inno_rag/manifest.sqlite")

    @property
    def codex_logs_dir(self) -> Path:
        return self.resolve_in_vault(self.inbox.codex_logs)

    @property
    def review_dir(self) -> Path:
        return self.resolve_in_vault(self.inbox.review)

    @property
    def processed_dir(self) -> Path:
        return self.resolve_in_vault(self.inbox.processed)

    @property
    def chroma_dir(self) -> Path:
        return self.resolve_data_path(self.rag.persist_dir)


def load_config(config_path: str | Path) -> AppConfig:
    raw_path = Path(config_path).expanduser().resolve()
    with raw_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise ConfigError("Top-level config must be a mapping")

    vault_path_str = raw.get("vault_path")
    if not isinstance(vault_path_str, str) or not vault_path_str.strip():
        raise ConfigError("Missing required string 'vault_path'")

    vault_path = Path(vault_path_str).expanduser().resolve()
    inbox_raw = _require_mapping(raw.get("inbox"), "inbox")
    nvidia_raw = _require_mapping(raw.get("nvidia"), "nvidia")
    rag_raw = _require_mapping(raw.get("rag"), "rag")
    safety_raw = _require_mapping(raw.get("safety"), "safety")

    inbox = InboxConfig(
        codex_logs=_require_str(inbox_raw, "codex_logs", "inbox"),
        review=_require_str(inbox_raw, "review", "inbox"),
        processed=_require_str(inbox_raw, "processed", "inbox"),
    )
    nvidia = NvidiaConfig(
        base_url=_require_str(nvidia_raw, "base_url", "nvidia"),
        llm_model=_require_str(nvidia_raw, "llm_model", "nvidia"),
        embedding_model=_require_str(nvidia_raw, "embedding_model", "nvidia"),
        rerank_model=str(nvidia_raw.get("rerank_model") or "").strip(),
        timeout_seconds=int(nvidia_raw.get("timeout_seconds", 60)),
    )
    rag = RagConfig(
        vector_db=_require_str(rag_raw, "vector_db", "rag"),
        persist_dir=_require_str(rag_raw, "persist_dir", "rag"),
        chunk_size=_require_int(rag_raw, "chunk_size", "rag"),
        chunk_overlap=_require_int(rag_raw, "chunk_overlap", "rag"),
        top_k=_require_int(rag_raw, "top_k", "rag"),
        rerank_top_k=_require_int(rag_raw, "rerank_top_k", "rag"),
        index_raw_codex_logs=bool(rag_raw.get("index_raw_codex_logs", False)),
        collection_name=str(rag_raw.get("collection_name") or "inno_obsidian_vault"),
    )
    safety = SafetyConfig(
        dry_run=_require_bool(safety_raw, "dry_run", "safety"),
        require_approval_for_apply=_require_bool(
            safety_raw, "require_approval_for_apply", "safety"
        ),
        append_only=_require_bool(safety_raw, "append_only", "safety"),
        redact_secrets=_require_bool(safety_raw, "redact_secrets", "safety"),
    )

    app_config = AppConfig(
        vault_path=vault_path,
        inbox=inbox,
        nvidia=nvidia,
        rag=rag,
        safety=safety,
        config_path=raw_path,
    )

    app_config.codex_logs_dir
    app_config.review_dir
    app_config.processed_dir
    app_config.chroma_dir

    return app_config
