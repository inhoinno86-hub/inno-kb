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
from inno_obsidian_ai.markdown_loader import load_markdown
from inno_obsidian_ai.proposal_parser import build_append_block, load_proposal


def append_text(path: Path, text: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if not existing.endswith("\n"):
            existing += "\n"
        path.write_text(existing + "\n" + text, encoding="utf-8")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "obsidian_ai.example.yaml"),
        help="Path to config YAML",
    )
    parser.add_argument("--write", action="store_true", help="Apply approved proposals")
    args = parser.parse_args()

    config = load_config(args.config)
    manifest = ManifestStore(config.manifest_path)
    dry_run = not args.write

    for proposal_path in sorted(config.review_dir.rglob("*.md")):
        proposal_doc = load_markdown(proposal_path, config.vault_path)
        proposal = load_proposal(config, proposal_path)

        if proposal.status != "approved":
            print(f"SKIP {proposal.relative_path} (status={proposal.status})")
            continue
        if not proposal.destinations:
            print(f"SKIP {proposal.relative_path} (no destinations)")
            continue
        if not manifest.needs_processing("proposal_apply", proposal.relative_path, proposal_doc.file_hash):
            print(f"SKIP {proposal.relative_path} (already applied)")
            continue

        block = build_append_block(proposal)
        target_rel_paths: list[str] = []
        for destination in proposal.destinations:
            target_path = config.resolve_in_vault(destination.relative_path)
            target_rel_paths.append(config.to_vault_relative(target_path))
            if dry_run:
                print(f"DRY-RUN append {proposal.relative_path} -> {target_rel_paths[-1]}")
                continue
            append_text(target_path, block)

        if not dry_run:
            manifest.record(
                "proposal_apply",
                proposal.relative_path,
                proposal_doc.file_hash,
                payload={
                    "source_file": proposal.source_file,
                    "targets": target_rel_paths,
                },
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
