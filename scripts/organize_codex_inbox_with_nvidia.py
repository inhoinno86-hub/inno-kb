#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from inno_obsidian_ai.config import load_config
from inno_obsidian_ai.manifest import ManifestStore
from inno_obsidian_ai.nvidia_client import (
    NVIDIAAPIKeyMissingError,
    NVIDIAClient,
    NVIDIAClientError,
)
from inno_obsidian_ai.organizer import organize_codex_logs


def _parse_since(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "obsidian_ai.example.yaml"),
        help="Path to config YAML",
    )
    parser.add_argument("--write", action="store_true", help="Write proposal files")
    parser.add_argument("--force", action="store_true", help="Regenerate proposals even when one already exists")
    parser.add_argument("--no-llm", action="store_true", help="Only print candidate files without creating proposals")
    parser.add_argument("--since", help="Only scan codex logs modified at or after the given ISO timestamp")
    parser.add_argument("--max-files", type=int, help="Hard limit for number of source files to process")
    return parser


def run_organizer(
    *,
    config,
    manifest: ManifestStore,
    write: bool,
    force: bool = False,
    no_llm: bool = False,
    since: datetime | None = None,
    max_files: int | None = None,
    pipeline_run_id: str = "",
) -> list:
    client = NVIDIAClient.from_config(config) if write and not no_llm else None
    return organize_codex_logs(
        config,
        client,
        manifest,
        dry_run=not write,
        since=since,
        max_files=max_files,
        force=force,
        no_llm=no_llm,
        pipeline_run_id=pipeline_run_id,
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        manifest = ManifestStore(config.manifest_path)
        results = run_organizer(
            config=config,
            manifest=manifest,
            write=args.write,
            force=args.force,
            no_llm=args.no_llm,
            since=_parse_since(args.since) if args.since else None,
            max_files=args.max_files,
            pipeline_run_id="",
        )
    except (NVIDIAAPIKeyMissingError, NVIDIAClientError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    for result in results:
        if result.skipped:
            print(f"SKIP {result.source_file} ({result.reason})")
        elif args.no_llm:
            print(f"CANDIDATE {result.source_file} -> {result.proposal_file} ({result.reason})")
        else:
            print(f"PROPOSAL {result.source_file} -> {result.proposal_file} ({result.reason})")

    print(f"Processed {len(results)} source files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
