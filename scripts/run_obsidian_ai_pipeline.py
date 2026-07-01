#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from apply_approved_proposals import apply_approved_proposals
from index_obsidian_vault import run_indexing
from organize_codex_inbox_with_nvidia import run_organizer
from inno_obsidian_ai.audit import AuditLogger
from inno_obsidian_ai.config import load_config
from inno_obsidian_ai.manifest import ManifestStore
from inno_obsidian_ai.pipeline import (
    PipelineSummary,
    append_operation_log,
    generate_run_id,
    parse_since,
    summarize_next_action,
    update_dashboard,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "obsidian_ai.example.yaml"),
        help="Path to config YAML",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan actions without writing files")
    parser.add_argument("--write", action="store_true", help="Allow file writes and NVIDIA-backed operations")
    parser.add_argument("--path-prefix", action="append", default=[], help="Restrict indexing to this path prefix")
    parser.add_argument("--organize-only", action="store_true", help="Run proposal generation only")
    parser.add_argument("--apply-only", action="store_true", help="Run approved proposal apply only")
    parser.add_argument("--index-only", action="store_true", help="Run incremental indexing only")
    parser.add_argument("--summary-only", action="store_true", help="Update operation log and dashboard only")
    parser.add_argument("--approved-only", action="store_true", help="Skip proposal generation and process approved proposals only")
    parser.add_argument("--since", help="Only scan codex logs modified at or after the given ISO timestamp")
    parser.add_argument("--stats", action="store_true", help="Print aggregated pipeline stats")
    parser.add_argument("--failed-only", action="store_true", help="Retry only files previously marked failed during index step")
    parser.add_argument("--max-files", type=int, help="Hard limit for files handled by a single step")
    parser.add_argument("--no-llm", action="store_true", help="Do not call the LLM; only print organize candidates")
    parser.add_argument("--audit-log", help="Custom audit log JSONL path, relative to the vault unless absolute")
    parser.add_argument("--force", action="store_true", help="Force proposal regeneration or reindex when supported")
    parser.add_argument(
        "--force-full-index",
        action="store_true",
        help="Allow full-vault index scan when config automation.allow_full_vault_index is true",
    )
    return parser


def _resolve_mode(args: argparse.Namespace) -> str:
    explicit_modes = [
        name
        for name, enabled in [
            ("organize-only", args.organize_only),
            ("apply-only", args.apply_only),
            ("index-only", args.index_only),
            ("summary-only", args.summary_only),
        ]
        if enabled
    ]
    if len(explicit_modes) > 1:
        raise ValueError("Only one of --organize-only, --apply-only, --index-only, --summary-only may be set.")
    if explicit_modes:
        return explicit_modes[0]
    if args.approved_only:
        return "approved-only"
    return "pipeline"


def _resolve_dry_run(args: argparse.Namespace) -> bool:
    if args.write and args.dry_run:
        raise ValueError("Cannot use --write and --dry-run together.")
    if args.write:
        return False
    return True


def _resolve_audit_log_path(config, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    return config.resolve_data_path(path)


def _resolve_path_prefixes(config, args: argparse.Namespace) -> list[str]:
    if args.path_prefix:
        return list(dict.fromkeys(args.path_prefix))
    return list(config.automation.default_index_path_prefixes)


def _guard_index_scope(config, *, path_prefixes: list[str], force_full_index: bool) -> None:
    if path_prefixes:
        return
    if not force_full_index:
        raise ValueError(
            "Full-vault indexing is blocked by default. Use --path-prefix or explicitly pass --force-full-index."
        )
    if not config.automation.allow_full_vault_index:
        raise ValueError("Full-vault indexing is disabled by config automation.allow_full_vault_index=false.")


def _print_summary(summary: PipelineSummary) -> None:
    print(
        "PIPELINE "
        f"run_id={summary.run_id} "
        f"mode={summary.mode} "
        f"scanned={summary.scanned_codex_logs} "
        f"proposals_created={summary.proposals_created} "
        f"proposal_candidates={summary.proposal_candidates} "
        f"proposals_applied={summary.proposals_applied} "
        f"notes_changed={summary.notes_changed} "
        f"indexed={summary.notes_indexed} "
        f"skipped={summary.skipped} "
        f"failed={summary.failed} "
        f"cleaned={summary.cleaned}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        mode = _resolve_mode(args)
        dry_run = _resolve_dry_run(args)
        config = load_config(args.config)
        manifest = ManifestStore(config.manifest_path)
        audit_log_path = _resolve_audit_log_path(config, args.audit_log)
        audit = AuditLogger(config.audit_log_dir, log_path=audit_log_path)
        run_id = generate_run_id()
        max_files = args.max_files if args.max_files is not None else config.automation.max_files_per_run
        path_prefixes = _resolve_path_prefixes(config, args)
        since = parse_since(args.since) if args.since else None
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    summary = PipelineSummary(
        run_id=run_id,
        mode=mode,
        write=not dry_run,
        dry_run=dry_run,
    )
    exit_code = 0

    run_organize = mode in {"pipeline", "organize-only"} and not args.approved_only
    run_apply = mode in {"pipeline", "apply-only", "approved-only"}
    run_index = mode == "index-only"
    run_summary = mode in {"pipeline", "summary-only", "approved-only"}

    if mode == "pipeline":
        run_organize = config.automation.organize_new_codex_logs and not args.approved_only
        run_apply = config.automation.apply_approved_proposals
        run_summary = config.automation.update_daily_log or config.automation.update_project_dashboard

    if run_organize:
        results = run_organizer(
            config=config,
            manifest=manifest,
            write=not dry_run,
            force=args.force,
            no_llm=args.no_llm,
            since=since,
            max_files=max_files,
            pipeline_run_id=run_id,
        )
        summary.scanned_codex_logs += len(results)
        summary.proposals_created += sum(1 for item in results if item.reason == "created")
        summary.proposal_candidates += sum(1 for item in results if item.reason in {"dry-run", "no-llm"})
        summary.skipped += sum(1 for item in results if item.skipped)

    apply_results = []
    if run_apply:
        apply_results = apply_approved_proposals(
            config,
            manifest,
            dry_run=dry_run,
            pipeline_run_id=run_id,
            audit_logger=audit,
        )
        summary.proposals_applied += sum(1 for item in apply_results if not item.skipped)
        changed_notes: list[str] = []
        for item in apply_results:
            changed_notes.extend(item.changed_notes)
        summary.changed_note_paths = list(dict.fromkeys(changed_notes))
        summary.notes_changed = len(summary.changed_note_paths)
        summary.skipped += sum(1 for item in apply_results if item.skipped)

    should_run_default_reindex = (
        mode in {"pipeline", "approved-only"}
        and config.automation.reindex_changed_notes
        and bool(summary.changed_note_paths)
    )
    if run_index or should_run_default_reindex:
        candidate_paths = summary.changed_note_paths if should_run_default_reindex else None
        if candidate_paths is None:
            try:
                _guard_index_scope(
                    config,
                    path_prefixes=path_prefixes,
                    force_full_index=args.force_full_index,
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                summary.failed += 1
                summary.warnings.append(str(exc))
                exit_code = 2
            else:
                index_result = run_indexing(
                    config,
                    write=not dry_run,
                    dry_run=dry_run,
                    path_prefixes=path_prefixes,
                    force=args.force,
                    failed_only=args.failed_only,
                    stats=args.stats,
                    candidate_paths=None,
                    manifest=manifest,
                    audit=audit,
                    audit_log_path=audit_log_path,
                    pipeline_run_id=run_id,
                )
                summary.notes_indexed += index_result.indexed_files
                summary.skipped += index_result.skipped_files
                summary.failed += index_result.failed_files
                summary.cleaned += index_result.cleaned_files
                exit_code = max(exit_code, index_result.exit_code)
        else:
            index_result = run_indexing(
                config,
                write=not dry_run,
                dry_run=dry_run,
                path_prefixes=path_prefixes,
                force=args.force,
                failed_only=False,
                stats=args.stats,
                candidate_paths=candidate_paths[:max_files] if max_files else candidate_paths,
                manifest=manifest,
                audit=audit,
                audit_log_path=audit_log_path,
                pipeline_run_id=run_id,
            )
            summary.notes_indexed += index_result.indexed_files
            summary.skipped += index_result.skipped_files
            summary.failed += index_result.failed_files
            summary.cleaned += index_result.cleaned_files
            exit_code = max(exit_code, index_result.exit_code)
    elif mode in {"pipeline", "index-only"} and not summary.changed_note_paths and not run_index:
        print("SKIP indexing (no changed notes)")

    summary.next_action = summarize_next_action(summary)

    if run_summary:
        if dry_run:
            if config.operation_log.enabled:
                print(f"DRY-RUN operation log -> {config.operation_log.destination}")
            if config.dashboard.enabled:
                print(f"DRY-RUN dashboard update -> {config.dashboard.path}")
        else:
            if config.automation.update_daily_log and config.operation_log.enabled:
                append_operation_log(config, summary)
            if config.automation.update_project_dashboard and config.dashboard.enabled:
                update_dashboard(
                    config,
                    manifest,
                    summary,
                    path_prefixes=path_prefixes,
                )

    if args.stats:
        _print_summary(summary)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
