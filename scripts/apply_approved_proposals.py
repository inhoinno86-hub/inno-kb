#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from inno_obsidian_ai.audit import AuditLogger
from inno_obsidian_ai.config import load_config
from inno_obsidian_ai.manifest import ManifestStore
from inno_obsidian_ai.markdown_loader import load_markdown, parse_frontmatter
from inno_obsidian_ai.proposal_parser import build_append_block, load_proposal


@dataclass(frozen=True)
class ApplyResult:
    proposal_file: str
    changed_notes: tuple[str, ...]
    skipped: bool
    reason: str


def append_text(path: Path, text: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if not existing.endswith("\n"):
            existing += "\n"
        path.write_text(existing + "\n" + text, encoding="utf-8")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _block_heading(block: str) -> str:
    for line in block.splitlines():
        if line.startswith("## "):
            return line.strip()
    return ""


def note_has_heading(path: Path, heading: str) -> bool:
    if not heading or not path.exists():
        return False
    return heading in path.read_text(encoding="utf-8")


def update_proposal_status(
    path: Path,
    *,
    status: str,
    applied_at: str,
    applied_run_id: str,
) -> None:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    if not frontmatter:
        raise ValueError(f"Proposal missing frontmatter: {path}")
    frontmatter["status"] = status
    frontmatter["applied_at"] = applied_at
    frontmatter["applied_run_id"] = applied_run_id
    rendered_frontmatter = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
    ).strip()
    path.write_text(f"---\n{rendered_frontmatter}\n---\n\n{body.lstrip()}", encoding="utf-8")


def apply_approved_proposals(
    config,
    manifest: ManifestStore,
    *,
    dry_run: bool,
    pipeline_run_id: str = "",
    audit_logger: AuditLogger | None = None,
) -> list[ApplyResult]:
    results: list[ApplyResult] = []
    for proposal_path in sorted(config.review_dir.rglob("*.md")):
        proposal_doc = load_markdown(proposal_path, config.vault_path)
        proposal = load_proposal(config, proposal_path)

        if proposal.status != "approved":
            reason = f"status={proposal.status}"
            print(f"SKIP {proposal.relative_path} ({reason})")
            if audit_logger is not None:
                audit_logger.log(
                    action="apply",
                    vault_relative_path=proposal.relative_path,
                    status="skipped",
                    file_hash=proposal_doc.file_hash,
                    run_id=pipeline_run_id,
                    extra={"reason": reason},
                )
            results.append(
                ApplyResult(
                    proposal_file=proposal.relative_path,
                    changed_notes=(),
                    skipped=True,
                    reason=reason,
                )
            )
            continue
        if not proposal.destinations:
            reason = "no destinations"
            print(f"SKIP {proposal.relative_path} ({reason})")
            results.append(
                ApplyResult(
                    proposal_file=proposal.relative_path,
                    changed_notes=(),
                    skipped=True,
                    reason=reason,
                )
            )
            continue

        block = build_append_block(proposal)
        heading = _block_heading(block)
        target_rel_paths: list[str] = []
        changed_notes: list[str] = []
        duplicate_only = True
        for destination in proposal.destinations:
            target_path = config.resolve_in_vault(destination.relative_path)
            target_relative = config.to_vault_relative(target_path)
            target_rel_paths.append(target_relative)

            if note_has_heading(target_path, heading):
                print(f"SKIP {proposal.relative_path} -> {target_relative} (duplicate heading)")
                continue

            duplicate_only = False
            if dry_run:
                print(f"DRY-RUN append {proposal.relative_path} -> {target_relative}")
            else:
                append_text(target_path, block)
                changed_notes.append(target_relative)

        if dry_run:
            if audit_logger is not None:
                audit_logger.log(
                    action="apply",
                    vault_relative_path=proposal.relative_path,
                    status="dry-run",
                    file_hash=proposal_doc.file_hash,
                    run_id=pipeline_run_id,
                    extra={"targets": target_rel_paths},
                )
            results.append(
                ApplyResult(
                    proposal_file=proposal.relative_path,
                    changed_notes=tuple(target_rel_paths),
                    skipped=False,
                    reason="dry-run",
                )
            )
            continue

        applied_at = datetime.now().astimezone().isoformat(timespec="seconds")
        update_proposal_status(
            proposal_path,
            status="applied",
            applied_at=applied_at,
            applied_run_id=pipeline_run_id,
        )
        updated_doc = load_markdown(proposal_path, config.vault_path)
        manifest.record(
            "proposal_apply",
            proposal.relative_path,
            updated_doc.file_hash,
            status="applied",
            payload={
                "source_file": proposal.source_file,
                "targets": target_rel_paths,
                "pipeline_run_id": pipeline_run_id,
            },
        )
        if audit_logger is not None:
            audit_logger.log(
                action="apply",
                vault_relative_path=proposal.relative_path,
                status="applied",
                file_hash=updated_doc.file_hash,
                run_id=pipeline_run_id,
                extra={"targets": target_rel_paths, "changed_notes": changed_notes},
            )
        results.append(
            ApplyResult(
                proposal_file=proposal.relative_path,
                changed_notes=tuple(changed_notes),
                skipped=False,
                reason="applied" if changed_notes else "already_present_marked_applied",
            )
        )
    return results


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

    apply_approved_proposals(
        config,
        manifest,
        dry_run=dry_run,
        pipeline_run_id="",
        audit_logger=None,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
