from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .config import AppConfig
from .markdown_loader import MarkdownDocument


@dataclass(frozen=True)
class IndexingDecision:
    note_type: str
    collection_name: str
    should_index: bool
    reason: str


def _matches_pattern(relative_path: str, pattern: str) -> bool:
    normalized = relative_path.strip("/")
    candidate = PurePosixPath(normalized)
    cleaned_pattern = pattern.strip("/")
    if candidate.match(cleaned_pattern):
        return True
    if cleaned_pattern.endswith("/**"):
        prefix = cleaned_pattern[:-3].rstrip("/")
        return normalized == prefix or normalized.startswith(f"{prefix}/")
    return fnmatch.fnmatchcase(normalized, cleaned_pattern)


def matches_any_pattern(relative_path: str, patterns: tuple[str, ...]) -> bool:
    return any(_matches_pattern(relative_path, pattern) for pattern in patterns)


def path_matches_prefixes(relative_path: str, prefixes: list[str] | tuple[str, ...] | None) -> bool:
    if not prefixes:
        return True
    return any(
        relative_path == prefix or relative_path.startswith(f"{prefix}/")
        for prefix in prefixes
    )


def should_index_path(
    config: AppConfig,
    relative_path: str,
    include_prefixes: list[str] | tuple[str, ...] | None = None,
) -> bool:
    if any(part.startswith(".") for part in Path(relative_path).parts):
        return False
    if not path_matches_prefixes(relative_path, include_prefixes):
        return False
    if matches_any_pattern(relative_path, config.indexing.exclude_patterns):
        return False
    if config.indexing.include_patterns and not matches_any_pattern(
        relative_path,
        config.indexing.include_patterns,
    ):
        return False
    return True


def infer_note_type(document: MarkdownDocument) -> str:
    raw_type = str(document.frontmatter.get("type", "")).strip()
    if raw_type:
        return raw_type

    parts = Path(document.relative_path).parts
    if len(parts) >= 2 and parts[0] == "00_Inbox" and parts[1] == "codex_logs":
        return "codex_session_log"
    if parts and parts[0] == "50_Decisions":
        return "decision"
    if parts and parts[0] == "20_Research":
        return "research"
    if parts and parts[0] == "30_Concepts":
        return "concept"
    if parts and parts[0] == "10_Projects":
        return "development_log"
    return "unknown"


def infer_project(document: MarkdownDocument) -> str:
    project = str(document.frontmatter.get("project", "")).strip()
    if project:
        return project

    parts = Path(document.relative_path).parts
    if len(parts) >= 2 and parts[0] == "10_Projects":
        return parts[1]
    return ""


def infer_source(document: MarkdownDocument) -> str:
    for key in ("source_file", "source", "source_path"):
        value = str(document.frontmatter.get(key, "")).strip()
        if value:
            return value
    return document.relative_path


def decide_indexing(
    config: AppConfig,
    document: MarkdownDocument,
    *,
    include_prefixes: list[str] | tuple[str, ...] | None = None,
    collection_filter: str | None = None,
) -> IndexingDecision:
    if not should_index_path(config, document.relative_path, include_prefixes):
        return IndexingDecision(
            note_type=infer_note_type(document),
            collection_name="",
            should_index=False,
            reason="path_filtered",
        )

    note_type = infer_note_type(document)
    policy = config.indexing.policy_for(note_type, config.rag.collection_name)
    if not policy.index:
        return IndexingDecision(
            note_type=note_type,
            collection_name=policy.collection,
            should_index=False,
            reason="note_type_disabled",
        )
    if collection_filter and policy.collection != collection_filter:
        return IndexingDecision(
            note_type=note_type,
            collection_name=policy.collection,
            should_index=False,
            reason="collection_filtered",
        )

    return IndexingDecision(
        note_type=note_type,
        collection_name=policy.collection,
        should_index=True,
        reason="selected",
    )
