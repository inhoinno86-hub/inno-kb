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


def _optional_patterns(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ConfigError(f"Expected list for '{field_name}'")

    patterns: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ConfigError(f"Expected non-empty string items for '{field_name}'")
        patterns.append(item.strip())
    return tuple(patterns)


def _optional_float(value: Any, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raise ConfigError(f"Expected number or null for '{field_name}'")


def _coerce_int(value: Any, field_name: str, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    raise ConfigError(f"Expected integer for '{field_name}'")


def _coerce_float(value: Any, field_name: str, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    raise ConfigError(f"Expected number for '{field_name}'")


def _coerce_bool(value: Any, field_name: str, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ConfigError(f"Expected boolean for '{field_name}'")


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
class NoteTypePolicy:
    index: bool
    collection: str


@dataclass(frozen=True)
class IndexingConfig:
    default_include_original_inbox_logs: bool
    include_patterns: tuple[str, ...]
    exclude_patterns: tuple[str, ...]
    note_type_policy: dict[str, NoteTypePolicy]

    def policy_for(self, note_type: str, default_collection: str) -> NoteTypePolicy:
        if note_type in self.note_type_policy:
            return self.note_type_policy[note_type]
        if "unknown" in self.note_type_policy:
            return self.note_type_policy["unknown"]
        return NoteTypePolicy(index=True, collection=default_collection)

    def collection_names(self, default_collection: str) -> tuple[str, ...]:
        names = {
            policy.collection
            for policy in self.note_type_policy.values()
            if policy.index and policy.collection
        }
        if not names:
            names.add(default_collection)
        return tuple(sorted(names))


@dataclass(frozen=True)
class EmbeddingConfig:
    batch_size: int
    max_retries: int
    retry_backoff_seconds: float
    timeout_seconds: int
    max_chunk_chars: int
    passage_input_type: str = "passage"
    query_input_type: str = "query"


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
    answer_format: str = "markdown_with_sources"
    min_evidence_score: float | None = None
    max_evidence_distance: float | None = 1.1
    require_sources: bool = True


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
    indexing: IndexingConfig
    embedding: EmbeddingConfig
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

    @property
    def audit_log_dir(self) -> Path:
        return self.resolve_data_path(".inno_rag/logs")

    @property
    def rag_collection_names(self) -> tuple[str, ...]:
        return self.indexing.collection_names(self.rag.collection_name)


def _default_note_type_policy(
    *,
    default_collection: str,
    default_include_original_inbox_logs: bool,
) -> dict[str, NoteTypePolicy]:
    raw_collection = "raw_codex_logs" if default_include_original_inbox_logs else default_collection
    return {
        "codex_session_log": NoteTypePolicy(
            index=default_include_original_inbox_logs,
            collection=raw_collection,
        ),
        "development_log": NoteTypePolicy(index=True, collection=default_collection),
        "decision": NoteTypePolicy(index=True, collection=default_collection),
        "research": NoteTypePolicy(index=True, collection=default_collection),
        "concept": NoteTypePolicy(index=True, collection=default_collection),
        "unknown": NoteTypePolicy(index=True, collection=default_collection),
    }


def _parse_note_type_policy(
    value: Any,
    *,
    default_collection: str,
    default_include_original_inbox_logs: bool,
) -> dict[str, NoteTypePolicy]:
    policies = _default_note_type_policy(
        default_collection=default_collection,
        default_include_original_inbox_logs=default_include_original_inbox_logs,
    )
    if value is None:
        return policies

    raw = _require_mapping(value, "indexing.note_type_policy")
    for note_type, policy_value in raw.items():
        if not isinstance(note_type, str) or not note_type.strip():
            raise ConfigError("Expected non-empty string keys for 'indexing.note_type_policy'")
        policy = _require_mapping(policy_value, f"indexing.note_type_policy.{note_type}")
        collection = str(policy.get("collection") or default_collection).strip()
        if not collection:
            raise ConfigError(
                f"Missing required string 'indexing.note_type_policy.{note_type}.collection'"
            )
        policies[note_type.strip()] = NoteTypePolicy(
            index=_coerce_bool(
                policy.get("index"),
                f"indexing.note_type_policy.{note_type}.index",
                True,
            ),
            collection=collection,
        )
    return policies


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
    indexing_raw = _require_mapping(raw.get("indexing") or {}, "indexing")
    embedding_raw = _require_mapping(raw.get("embedding") or {}, "embedding")
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
    default_include_original_inbox_logs = _coerce_bool(
        indexing_raw.get("default_include_original_inbox_logs"),
        "indexing.default_include_original_inbox_logs",
        bool(rag_raw.get("index_raw_codex_logs", False)),
    )
    default_exclude_patterns = [
        ".inno_rag/**",
        "99_Attachments/**",
        "00_Inbox/_review/**/*.md",
        "00_Inbox/_review_live_e2e/**/*.md",
        "00_Inbox/_processed/**/*.md",
    ]
    if not default_include_original_inbox_logs:
        default_exclude_patterns.insert(0, "00_Inbox/codex_logs/**/*.md")
    indexing = IndexingConfig(
        default_include_original_inbox_logs=default_include_original_inbox_logs,
        include_patterns=_optional_patterns(
            indexing_raw.get("include_patterns"),
            "indexing.include_patterns",
        ),
        exclude_patterns=tuple(
            dict.fromkeys(
                [
                    *default_exclude_patterns,
                    *_optional_patterns(
                        indexing_raw.get("exclude_patterns"),
                        "indexing.exclude_patterns",
                    ),
                ]
            )
        ),
        note_type_policy=_parse_note_type_policy(
            indexing_raw.get("note_type_policy"),
            default_collection=str(rag_raw.get("collection_name") or "inno_obsidian_vault"),
            default_include_original_inbox_logs=default_include_original_inbox_logs,
        ),
    )
    embedding = EmbeddingConfig(
        batch_size=_coerce_int(embedding_raw.get("batch_size"), "embedding.batch_size", 1),
        max_retries=_coerce_int(embedding_raw.get("max_retries"), "embedding.max_retries", 3),
        retry_backoff_seconds=_coerce_float(
            embedding_raw.get("retry_backoff_seconds"),
            "embedding.retry_backoff_seconds",
            2.0,
        ),
        timeout_seconds=_coerce_int(
            embedding_raw.get("timeout_seconds"),
            "embedding.timeout_seconds",
            nvidia.timeout_seconds,
        ),
        max_chunk_chars=_coerce_int(
            embedding_raw.get("max_chunk_chars"),
            "embedding.max_chunk_chars",
            int(rag_raw.get("chunk_size", 500)),
        ),
        passage_input_type=str(embedding_raw.get("passage_input_type") or "passage").strip()
        or "passage",
        query_input_type=str(embedding_raw.get("query_input_type") or "query").strip()
        or "query",
    )
    rag = RagConfig(
        vector_db=_require_str(rag_raw, "vector_db", "rag"),
        persist_dir=_require_str(rag_raw, "persist_dir", "rag"),
        chunk_size=_coerce_int(
            rag_raw.get("chunk_size"),
            "rag.chunk_size",
            embedding.max_chunk_chars,
        ),
        chunk_overlap=_coerce_int(rag_raw.get("chunk_overlap"), "rag.chunk_overlap", 200),
        top_k=_require_int(rag_raw, "top_k", "rag"),
        rerank_top_k=_require_int(rag_raw, "rerank_top_k", "rag"),
        index_raw_codex_logs=default_include_original_inbox_logs,
        collection_name=str(rag_raw.get("collection_name") or "inno_obsidian_vault"),
        answer_format=str(rag_raw.get("answer_format") or "markdown_with_sources").strip()
        or "markdown_with_sources",
        min_evidence_score=_optional_float(
            rag_raw.get("min_evidence_score"),
            "rag.min_evidence_score",
        ),
        max_evidence_distance=_optional_float(
            rag_raw.get("max_evidence_distance"),
            "rag.max_evidence_distance",
        )
        if "max_evidence_distance" in rag_raw
        else 1.1,
        require_sources=_coerce_bool(
            rag_raw.get("require_sources"),
            "rag.require_sources",
            True,
        ),
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
        indexing=indexing,
        embedding=embedding,
        rag=rag,
        safety=safety,
        config_path=raw_path,
    )

    app_config.codex_logs_dir
    app_config.review_dir
    app_config.processed_dir
    app_config.chroma_dir
    app_config.audit_log_dir

    return app_config
