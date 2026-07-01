#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from inno_obsidian_ai.chunker import chunk_markdown
from inno_obsidian_ai.config import load_config
from inno_obsidian_ai.manifest import ManifestStore
from inno_obsidian_ai.markdown_loader import load_markdown
from inno_obsidian_ai.nvidia_client import (
    NVIDIAAPIKeyMissingError,
    NVIDIAClient,
    NVIDIAClientError,
)
from inno_obsidian_ai.vector_store import ChromaVectorStore


def should_index(config, relative_path: str, include_prefixes: list[str] | None = None) -> bool:
    parts = Path(relative_path).parts
    if any(part.startswith(".") for part in Path(relative_path).parts):
        return False
    if len(parts) >= 2 and parts[0] == "00_Inbox" and (
        parts[1] == "codex_logs" and not config.rag.index_raw_codex_logs
    ):
        return False
    if len(parts) >= 2 and parts[0] == "00_Inbox" and (
        parts[1].startswith("_review") or parts[1].startswith("_processed")
    ):
        return False
    if include_prefixes and not any(
        relative_path == prefix or relative_path.startswith(f"{prefix}/")
        for prefix in include_prefixes
    ):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "obsidian_ai.example.yaml"),
        help="Path to config YAML",
    )
    parser.add_argument("--write", action="store_true", help="Persist embeddings to Chroma")
    parser.add_argument(
        "--path-prefix",
        action="append",
        default=[],
        help="Only index files whose vault-relative path matches this prefix",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        manifest = ManifestStore(config.manifest_path)
        dry_run = not args.write
        client = NVIDIAClient.from_config(config) if not dry_run else None
        store = None if dry_run else ChromaVectorStore(
            persist_dir=str(config.chroma_dir),
            collection_name=config.rag.collection_name,
        )
    except (NVIDIAAPIKeyMissingError, NVIDIAClientError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    indexed = 0
    for markdown_path in sorted(config.vault_path.rglob("*.md")):
        document = load_markdown(markdown_path, config.vault_path)
        if not should_index(config, document.relative_path, args.path_prefix):
            continue
        if not manifest.needs_processing("index_source", document.relative_path, document.file_hash):
            print(f"SKIP {document.relative_path} (unchanged)")
            continue

        chunks = chunk_markdown(document, config.rag.chunk_size, config.rag.chunk_overlap)
        if not chunks:
            print(f"SKIP {document.relative_path} (empty)")
            continue

        if dry_run:
            print(f"DRY-RUN index {document.relative_path} ({len(chunks)} chunks)")
            indexed += 1
            continue

        try:
            embeddings = client.embed_texts(
                [chunk.text for chunk in chunks],
                input_type="passage",
            )
            metadatas = []
            for chunk in chunks:
                metadatas.append(
                    {
                        "source": document.relative_path,
                        "file_name": Path(document.relative_path).name,
                        "heading": chunk.heading,
                        "project": str(document.frontmatter.get("project", "")),
                        "type": str(document.frontmatter.get("type", "")),
                        "date": str(
                            document.frontmatter.get("date", document.frontmatter.get("created_at", ""))
                        ),
                        "hash": document.file_hash,
                    }
                )

            ids = [f"{document.relative_path}:{chunk.index}:{document.file_hash[:8]}" for chunk in chunks]
            store.delete_source(document.relative_path)
            store.upsert(
                ids=ids,
                documents=[chunk.text for chunk in chunks],
                metadatas=metadatas,
                embeddings=embeddings,
            )
            manifest.record("index_source", document.relative_path, document.file_hash)
            indexed += 1
            print(f"INDEXED {document.relative_path} ({len(chunks)} chunks)")
        except NVIDIAClientError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    print(f"Indexed files: {indexed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
