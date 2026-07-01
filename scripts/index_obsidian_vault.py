#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from inno_obsidian_ai.audit import AuditLogger
from inno_obsidian_ai.chunker import chunk_markdown
from inno_obsidian_ai.config import AppConfig, load_config
from inno_obsidian_ai.indexing import (
    decide_indexing,
    infer_project,
    infer_source,
    should_index_path,
)
from inno_obsidian_ai.manifest import IndexedChunkRecord, IndexedFileRecord, ManifestStore
from inno_obsidian_ai.markdown_loader import MarkdownDocument, iter_markdown_files, load_markdown
from inno_obsidian_ai.nvidia_client import (
    NVIDIAAPIKeyMissingError,
    NVIDIAClient,
    NVIDIAClientError,
)
from inno_obsidian_ai.safety import redact_secrets, sha256_text
from inno_obsidian_ai.vector_store import ChromaVectorStore


@dataclass(frozen=True)
class PreparedChunk:
    chunk_id: str
    text: str
    metadata: dict[str, str]
    manifest_record: IndexedChunkRecord


@dataclass(frozen=True)
class IndexJob:
    document: MarkdownDocument
    note_type: str
    project: str
    source: str
    collection_name: str
    path_hash: str
    file_size: int
    modified_time: float
    chunks: list[PreparedChunk]
    reindex_reason: str


@dataclass(frozen=True)
class IndexRunResult:
    target_files: int
    skipped_files: int
    indexed_files: int
    failed_files: int
    estimated_chunks: int
    cleaned_files: int
    dry_run: bool
    exit_code: int


def should_index(config: AppConfig, relative_path: str, include_prefixes: list[str] | None = None) -> bool:
    return should_index_path(config, relative_path, include_prefixes)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "obsidian_ai.example.yaml"),
        help="Path to config YAML",
    )
    parser.add_argument("--write", action="store_true", help="Persist embeddings to Chroma")
    parser.add_argument("--dry-run", action="store_true", help="Do not call NVIDIA APIs or write data")
    parser.add_argument(
        "--path-prefix",
        action="append",
        default=[],
        help="Only index files whose vault-relative path matches this prefix",
    )
    parser.add_argument("--collection", help="Only process files mapped to this collection")
    parser.add_argument("--force", action="store_true", help="Reindex even when file_hash matches")
    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="Retry only files whose previous index_status was failed",
    )
    parser.add_argument("--stats", action="store_true", help="Print summary statistics")
    parser.add_argument(
        "--cleanup-missing",
        action="store_true",
        help="Delete vector entries and manifest rows for missing or excluded files",
    )
    return parser


def _store_for(
    cache: dict[str, ChromaVectorStore],
    *,
    config: AppConfig,
    collection_name: str,
) -> ChromaVectorStore:
    if collection_name not in cache:
        cache[collection_name] = ChromaVectorStore(
            persist_dir=str(config.chroma_dir),
            collection_name=collection_name,
        )
    return cache[collection_name]


def _build_prepared_chunks(
    config: AppConfig,
    document: MarkdownDocument,
    *,
    note_type: str,
    project: str,
    collection_name: str,
) -> list[PreparedChunk]:
    chunk_size = min(config.rag.chunk_size, config.embedding.max_chunk_chars)
    raw_chunks = chunk_markdown(document, chunk_size, config.rag.chunk_overlap)
    prepared: list[PreparedChunk] = []
    seen_chunk_hashes: set[str] = set()
    for chunk in raw_chunks:
        metadata = {
            "source": document.relative_path,
            "file_name": Path(document.relative_path).name,
            "heading": chunk.heading,
            "project": project,
            "type": note_type,
            "collection": collection_name,
            "date": str(document.frontmatter.get("date", document.frontmatter.get("created_at", ""))),
            "hash": document.file_hash,
        }
        content_hash = sha256_text(chunk.text)
        metadata_hash = sha256_text(json.dumps(metadata, ensure_ascii=False, sort_keys=True))
        chunk_hash = sha256_text(f"{content_hash}:{metadata_hash}")
        if chunk_hash in seen_chunk_hashes:
            continue
        seen_chunk_hashes.add(chunk_hash)
        chunk_id = sha256_text(
            f"{document.relative_path}:{collection_name}:{config.nvidia.embedding_model}:{chunk.index}:{chunk_hash}"
        )[:32]
        prepared.append(
            PreparedChunk(
                chunk_id=chunk_id,
                text=chunk.text,
                metadata=metadata,
                manifest_record=IndexedChunkRecord(
                    chunk_id=chunk_id,
                    vault_relative_path=document.relative_path,
                    heading=chunk.heading,
                    chunk_index=chunk.index,
                    chunk_hash=chunk_hash,
                    content_hash=content_hash,
                    metadata_hash=metadata_hash,
                    embedding_model=config.nvidia.embedding_model,
                    collection_name=collection_name,
                    indexed_at="",
                ),
            )
        )
    return prepared


def _build_job(
    config: AppConfig,
    manifest: ManifestStore,
    document: MarkdownDocument,
    *,
    collection_filter: str | None,
    include_prefixes: list[str],
    force: bool,
) -> IndexJob | None:
    decision = decide_indexing(
        config,
        document,
        include_prefixes=include_prefixes,
        collection_filter=collection_filter,
    )
    if not decision.should_index:
        return None

    project = infer_project(document)
    source = infer_source(document)
    stat = document.path.stat()
    chunks = _build_prepared_chunks(
        config,
        document,
        note_type=decision.note_type,
        project=project,
        collection_name=decision.collection_name,
    )
    needs_reindex, reason = manifest.should_reindex_file(
        document.relative_path,
        file_hash=document.file_hash,
        embedding_model=config.nvidia.embedding_model,
        collection_name=decision.collection_name,
        force=force,
    )
    if not needs_reindex:
        return None

    return IndexJob(
        document=document,
        note_type=decision.note_type,
        project=project,
        source=source,
        collection_name=decision.collection_name,
        path_hash=sha256_text(document.relative_path),
        file_size=stat.st_size,
        modified_time=stat.st_mtime,
        chunks=chunks,
        reindex_reason=reason,
    )


def _cleanup_candidates(
    config: AppConfig,
    manifest: ManifestStore,
    *,
    include_prefixes: list[str],
    collection_filter: str | None,
) -> list[tuple[IndexedFileRecord, str]]:
    candidates: list[tuple[IndexedFileRecord, str]] = []
    for record in manifest.list_indexed_files(
        path_prefixes=include_prefixes,
        collection_name=collection_filter,
    ):
        path = config.resolve_in_vault(record.vault_relative_path)
        if not path.exists():
            candidates.append((record, "missing"))
            continue
        if not should_index(config, record.vault_relative_path, include_prefixes):
            candidates.append((record, "excluded"))
            continue

        document = load_markdown(path, config.vault_path)
        decision = decide_indexing(
            config,
            document,
            include_prefixes=include_prefixes,
            collection_filter=collection_filter,
        )
        if not decision.should_index:
            candidates.append((record, "excluded"))
    return candidates


def _process_cleanup(
    config: AppConfig,
    manifest: ManifestStore,
    audit: AuditLogger,
    *,
    include_prefixes: list[str],
    collection_filter: str | None,
    dry_run: bool,
    store_cache: dict[str, ChromaVectorStore],
    pipeline_run_id: str = "",
) -> int:
    cleaned = 0
    for record, reason in _cleanup_candidates(
        config,
        manifest,
        include_prefixes=include_prefixes,
        collection_filter=collection_filter,
    ):
        if dry_run:
            print(
                f"DRY-RUN cleanup {record.vault_relative_path} "
                f"(reason={reason}, collection={record.collection_name})"
            )
            continue

        store = _store_for(
            store_cache,
            config=config,
            collection_name=record.collection_name,
        )
        store.delete_source(record.vault_relative_path)
        manifest.delete_indexed_file(record.vault_relative_path)
        audit.log(
            action="cleanup",
            vault_relative_path=record.vault_relative_path,
            status=reason,
            file_hash=record.file_hash,
            chunk_count=record.chunk_count,
            collection=record.collection_name,
            model=record.embedding_model,
            run_id=pipeline_run_id,
        )
        cleaned += 1
        print(
            f"CLEANUP {record.vault_relative_path} "
            f"(reason={reason}, collection={record.collection_name})"
        )
    return cleaned


def _print_stats(
    *,
    target_files: int,
    skipped_files: int,
    indexed_files: int,
    failed_files: int,
    estimated_chunks: int,
    cleaned_files: int,
) -> None:
    print(
        "STATS "
        f"target_files={target_files} "
        f"skipped={skipped_files} "
        f"indexed={indexed_files} "
        f"failed={failed_files} "
        f"estimated_chunks={estimated_chunks} "
        f"cleaned={cleaned_files}"
    )


def _iter_scan_paths(config: AppConfig, candidate_paths: list[str] | tuple[str, ...] | None) -> list[Path]:
    if candidate_paths is None:
        return list(iter_markdown_files(config.vault_path))

    resolved: list[Path] = []
    seen: set[str] = set()
    for relative_path in candidate_paths:
        if relative_path in seen:
            continue
        seen.add(relative_path)
        path = config.resolve_in_vault(relative_path)
        if not path.exists() or path.suffix.lower() != ".md":
            continue
        resolved.append(path)
    return resolved


def run_indexing(
    config: AppConfig,
    *,
    write: bool,
    dry_run: bool = False,
    path_prefixes: list[str] | None = None,
    collection: str | None = None,
    force: bool = False,
    failed_only: bool = False,
    stats: bool = False,
    cleanup_missing: bool = False,
    candidate_paths: list[str] | tuple[str, ...] | None = None,
    manifest: ManifestStore | None = None,
    audit: AuditLogger | None = None,
    audit_log_path: Path | None = None,
    pipeline_run_id: str = "",
) -> IndexRunResult:
    if write and dry_run:
        raise ValueError("Cannot use --write and --dry-run together.")

    effective_dry_run = not write or dry_run
    manifest = manifest or ManifestStore(config.manifest_path)
    audit = audit or AuditLogger(config.audit_log_dir, log_path=audit_log_path)

    store_cache: dict[str, ChromaVectorStore] = {}
    client: NVIDIAClient | None = None
    indexed_files = 0
    failed_files = 0
    skipped_files = 0
    cleaned_files = 0
    estimated_chunks = 0
    jobs: list[IndexJob] = []
    failed_records = {
        record.vault_relative_path
        for record in manifest.list_indexed_files(index_status="failed")
    }

    for markdown_path in _iter_scan_paths(config, candidate_paths):
        relative_path = config.to_vault_relative(markdown_path)
        if not should_index(config, relative_path, path_prefixes):
            continue

        document = load_markdown(markdown_path, config.vault_path)
        decision = decide_indexing(
            config,
            document,
            include_prefixes=path_prefixes,
            collection_filter=collection,
        )
        if not decision.should_index:
            continue

        if failed_only and document.relative_path not in failed_records:
            continue

        job = _build_job(
            config,
            manifest,
            document,
            collection_filter=collection,
            include_prefixes=path_prefixes or [],
            force=force,
        )
        if job is None:
            skipped_files += 1
            print(f"SKIP {document.relative_path} (unchanged)")
            audit.log(
                action="index",
                vault_relative_path=document.relative_path,
                status="skipped",
                file_hash=document.file_hash,
                collection=decision.collection_name,
                model=config.nvidia.embedding_model,
                run_id=pipeline_run_id,
            )
            continue

        jobs.append(job)
        estimated_chunks += len(job.chunks)
        if effective_dry_run:
            print(
                f"DRY-RUN index {job.document.relative_path} "
                f"(collection={job.collection_name}, chunks={len(job.chunks)}, reason={job.reindex_reason})"
            )

    if cleanup_missing:
        try:
            cleaned_files = _process_cleanup(
                config,
                manifest,
                audit,
                include_prefixes=path_prefixes or [],
                collection_filter=collection,
                dry_run=effective_dry_run,
                store_cache=store_cache,
                pipeline_run_id=pipeline_run_id,
            )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return IndexRunResult(
                target_files=len(jobs),
                skipped_files=skipped_files,
                indexed_files=indexed_files,
                failed_files=failed_files,
                estimated_chunks=estimated_chunks,
                cleaned_files=cleaned_files,
                dry_run=effective_dry_run,
                exit_code=2,
            )

    if not effective_dry_run:
        try:
            if jobs:
                client = NVIDIAClient.from_config(config)
        except (NVIDIAAPIKeyMissingError, NVIDIAClientError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return IndexRunResult(
                target_files=len(jobs),
                skipped_files=skipped_files,
                indexed_files=indexed_files,
                failed_files=failed_files,
                estimated_chunks=estimated_chunks,
                cleaned_files=cleaned_files,
                dry_run=effective_dry_run,
                exit_code=2,
            )

        for job in jobs:
            existing = manifest.get_indexed_file(job.document.relative_path)
            old_collection = existing.collection_name if existing is not None else ""
            try:
                if old_collection and old_collection != job.collection_name:
                    _store_for(
                        store_cache,
                        config=config,
                        collection_name=old_collection,
                    ).delete_source(job.document.relative_path)

                current_store = _store_for(
                    store_cache,
                    config=config,
                    collection_name=job.collection_name,
                )
                current_store.delete_source(job.document.relative_path)

                embeddings = client.embed_texts(
                    [chunk.text for chunk in job.chunks],
                    input_type=config.embedding.passage_input_type,
                ) if job.chunks else []

                if job.chunks:
                    current_store.upsert(
                        ids=[chunk.chunk_id for chunk in job.chunks],
                        documents=[chunk.text for chunk in job.chunks],
                        metadatas=[chunk.metadata for chunk in job.chunks],
                        embeddings=embeddings,
                    )

                indexed_at = datetime.now(timezone.utc).isoformat()
                manifest.upsert_indexed_file(
                    IndexedFileRecord(
                        vault_relative_path=job.document.relative_path,
                        path_hash=job.path_hash,
                        file_hash=job.document.file_hash,
                        file_size=job.file_size,
                        modified_time=job.modified_time,
                        note_type=job.note_type,
                        project=job.project,
                        source=job.source,
                        indexed_at=indexed_at,
                        index_status="indexed",
                        last_error="",
                        collection_name=job.collection_name,
                        embedding_model=config.nvidia.embedding_model,
                        chunk_count=len(job.chunks),
                        payload={"reason": job.reindex_reason},
                    ),
                    chunks=[
                        IndexedChunkRecord(
                            chunk_id=chunk.manifest_record.chunk_id,
                            vault_relative_path=chunk.manifest_record.vault_relative_path,
                            heading=chunk.manifest_record.heading,
                            chunk_index=chunk.manifest_record.chunk_index,
                            chunk_hash=chunk.manifest_record.chunk_hash,
                            content_hash=chunk.manifest_record.content_hash,
                            metadata_hash=chunk.manifest_record.metadata_hash,
                            embedding_model=chunk.manifest_record.embedding_model,
                            collection_name=chunk.manifest_record.collection_name,
                            indexed_at=indexed_at,
                        )
                        for chunk in job.chunks
                    ],
                )
                manifest.record(
                    "index_source",
                    job.document.relative_path,
                    job.document.file_hash,
                    status="processed",
                    payload={
                        "collection_name": job.collection_name,
                        "embedding_model": config.nvidia.embedding_model,
                        "chunk_count": len(job.chunks),
                    },
                )
                audit.log(
                    action="index",
                    vault_relative_path=job.document.relative_path,
                    status="indexed",
                    file_hash=job.document.file_hash,
                    chunk_count=len(job.chunks),
                    collection=job.collection_name,
                    model=config.nvidia.embedding_model,
                    run_id=pipeline_run_id,
                    extra={"reason": job.reindex_reason},
                )
                indexed_files += 1
                print(
                    f"INDEXED {job.document.relative_path} "
                    f"(collection={job.collection_name}, chunks={len(job.chunks)})"
                )
            except (NVIDIAClientError, RuntimeError) as exc:
                error = redact_secrets(str(exc), enabled=True)
                manifest.mark_index_failed(
                    vault_relative_path=job.document.relative_path,
                    path_hash=job.path_hash,
                    file_hash=job.document.file_hash,
                    file_size=job.file_size,
                    modified_time=job.modified_time,
                    note_type=job.note_type,
                    project=job.project,
                    source=job.source,
                    collection_name=job.collection_name,
                    embedding_model=config.nvidia.embedding_model,
                    last_error=error,
                    payload={"reason": job.reindex_reason},
                )
                manifest.record(
                    "index_source",
                    job.document.relative_path,
                    job.document.file_hash,
                    status="failed",
                    payload={"error": error},
                )
                audit.log(
                    action="index",
                    vault_relative_path=job.document.relative_path,
                    status="failed",
                    file_hash=job.document.file_hash,
                    chunk_count=len(job.chunks),
                    collection=job.collection_name,
                    model=config.nvidia.embedding_model,
                    error=error,
                    run_id=pipeline_run_id,
                    extra={"reason": job.reindex_reason},
                )
                failed_files += 1
                print(f"FAILED {job.document.relative_path} ({error})", file=sys.stderr)

    result = IndexRunResult(
        target_files=len(jobs),
        skipped_files=skipped_files,
        indexed_files=indexed_files,
        failed_files=failed_files,
        estimated_chunks=estimated_chunks,
        cleaned_files=cleaned_files,
        dry_run=effective_dry_run,
        exit_code=0 if failed_files == 0 else 2,
    )
    if stats:
        _print_stats(
            target_files=result.target_files,
            skipped_files=result.skipped_files,
            indexed_files=result.indexed_files,
            failed_files=result.failed_files,
            estimated_chunks=result.estimated_chunks,
            cleaned_files=result.cleaned_files,
        )
    else:
        print(f"Indexed files: {indexed_files}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        result = run_indexing(
            config,
            write=args.write,
            dry_run=args.dry_run,
            path_prefixes=args.path_prefix,
            collection=args.collection,
            force=args.force,
            failed_only=args.failed_only,
            stats=args.stats,
            cleanup_missing=args.cleanup_missing,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
