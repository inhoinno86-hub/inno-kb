#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "obsidian_ai.example.yaml"),
        help="Path to config YAML",
    )
    parser.add_argument("--write", action="store_true", help="Write proposal files")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        manifest = ManifestStore(config.manifest_path)
        client = NVIDIAClient.from_config(config) if args.write else None
        results = organize_codex_logs(config, client, manifest, dry_run=not args.write)
    except (NVIDIAAPIKeyMissingError, NVIDIAClientError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    for result in results:
        if result.skipped:
            print(f"SKIP {result.source_file} ({result.reason})")
        else:
            print(f"PROPOSAL {result.source_file} -> {result.proposal_file} ({result.reason})")

    print(f"Processed {len(results)} source files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
