from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .config import AppConfig
from .manifest import ManifestStore
from .markdown_loader import load_markdown
from .proposal_parser import ProposalDocument, load_proposal
from .safety import redact_secrets


@dataclass
class PipelineSummary:
    run_id: str
    mode: str
    write: bool
    dry_run: bool
    scanned_codex_logs: int = 0
    proposals_created: int = 0
    proposal_candidates: int = 0
    proposals_applied: int = 0
    notes_changed: int = 0
    notes_indexed: int = 0
    skipped: int = 0
    failed: int = 0
    cleaned: int = 0
    warnings: list[str] = field(default_factory=list)
    next_action: str = "No action"
    changed_note_paths: list[str] = field(default_factory=list)


def generate_run_id(now: datetime | None = None) -> str:
    timestamp = (now or datetime.now().astimezone()).strftime("%Y%m%d-%H%M%S")
    return f"obsidian-ai-{timestamp}"


def parse_since(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized)


def render_operation_log(summary: PipelineSummary, *, timestamp: datetime | None = None) -> str:
    rendered_at = (timestamp or datetime.now().astimezone()).strftime("%Y-%m-%d %H:%M")
    warning_text = "; ".join(summary.warnings) if summary.warnings else "none"
    lines = [
        f"## Obsidian AI Pipeline - {rendered_at}",
        "",
        f"* Run ID: {summary.run_id}",
        f"* Mode: {summary.mode}",
        f"* Write enabled: {'yes' if summary.write else 'no'}",
        f"* Codex logs scanned: {summary.scanned_codex_logs}",
        f"* Proposals created: {summary.proposals_created}",
        f"* Proposal candidates: {summary.proposal_candidates}",
        f"* Proposals applied: {summary.proposals_applied}",
        f"* Notes changed: {summary.notes_changed}",
        f"* Notes indexed: {summary.notes_indexed}",
        f"* Skipped: {summary.skipped}",
        f"* Failed: {summary.failed}",
        f"* Cleanup: {summary.cleaned}",
        f"* Warnings: {redact_secrets(warning_text, enabled=True)}",
        f"* Next action: {redact_secrets(summary.next_action, enabled=True)}",
        "",
    ]
    return "\n".join(lines)


def append_operation_log(config: AppConfig, summary: PipelineSummary) -> Path | None:
    destination = config.operation_log_path
    if destination is None:
        return None
    block = render_operation_log(summary)
    if destination.exists():
        existing = destination.read_text(encoding="utf-8")
        if not existing.endswith("\n"):
            existing += "\n"
        destination.write_text(existing + "\n" + block, encoding="utf-8")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(block, encoding="utf-8")
    return destination


def _recent_codex_logs(config: AppConfig, limit: int = 5) -> list[str]:
    files = sorted(
        config.codex_logs_dir.rglob("*.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return [config.to_vault_relative(path) for path in files[:limit]]


def _load_proposals(config: AppConfig) -> list[ProposalDocument]:
    proposals: list[ProposalDocument] = []
    for proposal_path in sorted(config.review_dir.rglob("*.proposal.md")):
        try:
            proposals.append(load_proposal(config, proposal_path))
        except ValueError:
            continue
    return proposals


def _proposal_status_counts(proposals: list[ProposalDocument]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for proposal in proposals:
        counts[proposal.status] = counts.get(proposal.status, 0) + 1
    return counts


def _summarize_section_lines(text: str, *, limit: int = 3) -> list[str]:
    lines = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            lines.append(redact_secrets(stripped, enabled=True))
        else:
            lines.append(redact_secrets(f"- {stripped}", enabled=True))
        if len(lines) >= limit:
            break
    return lines


def _recent_applied_summaries(proposals: list[ProposalDocument], limit: int = 3) -> list[str]:
    applied = [proposal for proposal in proposals if proposal.status == "applied"]
    applied.sort(key=lambda item: item.created_at, reverse=True)
    lines: list[str] = []
    for proposal in applied[:limit]:
        decisions = _summarize_section_lines(proposal.sections.get("Decisions", ""))
        todos = _summarize_section_lines(proposal.sections.get("TODO", ""))
        if not decisions and not todos:
            continue
        lines.append(f"- {proposal.feature} ({proposal.relative_path})")
        lines.extend(decisions[:2] or ["- Decisions: 확인 필요"])
        lines.extend(todos[:2] or ["- TODO: 확인 필요"])
    return lines[: max(limit * 3, 1)]


def _index_status_lines(
    manifest: ManifestStore,
    *,
    path_prefixes: list[str] | tuple[str, ...] | None,
    limit: int = 5,
) -> tuple[list[str], list[str]]:
    records = manifest.list_indexed_files(path_prefixes=path_prefixes)
    indexed = [record for record in records if record.index_status == "indexed"]
    failed = [record for record in records if record.index_status == "failed"]
    indexed.sort(key=lambda item: item.indexed_at, reverse=True)
    failed.sort(key=lambda item: item.indexed_at, reverse=True)
    indexed_lines = [
        f"- {record.vault_relative_path} ({record.collection_name}, chunks={record.chunk_count})"
        for record in indexed[:limit]
    ]
    failed_lines = [
        f"- {record.vault_relative_path} ({redact_secrets(record.last_error, enabled=True) or 'failed'})"
        for record in failed[:limit]
    ]
    return indexed_lines, failed_lines


def _replace_marker_section(
    existing: str,
    *,
    start_marker: str,
    end_marker: str,
    replacement_body: str,
) -> str:
    block = f"{start_marker}\n{replacement_body.rstrip()}\n{end_marker}"
    if start_marker in existing and end_marker in existing:
        start_index = existing.index(start_marker)
        end_index = existing.index(end_marker, start_index) + len(end_marker)
        return existing[:start_index] + block + existing[end_index:]

    suffix = "" if not existing or existing.endswith("\n") else "\n"
    return f"{existing}{suffix}\n{block}\n".lstrip("\n")


def render_dashboard_section(
    config: AppConfig,
    manifest: ManifestStore,
    summary: PipelineSummary,
    *,
    path_prefixes: list[str] | tuple[str, ...] | None = None,
) -> str:
    proposals = _load_proposals(config)
    counts = _proposal_status_counts(proposals)
    recent_logs = _recent_codex_logs(config)
    recent_applied = _recent_applied_summaries(proposals)
    indexed_lines, failed_lines = _index_status_lines(manifest, path_prefixes=path_prefixes)

    lines = [
        "## Obsidian AI Auto Summary",
        "",
        f"- Last run: {summary.run_id}",
        f"- Mode: {summary.mode}",
        f"- Notes changed this run: {summary.notes_changed}",
        f"- Notes indexed this run: {summary.notes_indexed}",
        "",
        "### Recent Codex Logs",
        *(recent_logs or ["- none"]),
        "",
        "### Proposal Status",
        f"- review: {counts.get('review', 0)}",
        f"- approved: {counts.get('approved', 0)}",
        f"- applied: {counts.get('applied', 0)}",
        f"- rejected: {counts.get('rejected', 0)}",
        "",
        "### Recent Applied Decisions / TODO",
        *(recent_applied or ["- none"]),
        "",
        "### Recent RAG Index Status",
        *(indexed_lines or ["- none"]),
        "",
        "### Failed Items",
        *(failed_lines or ["- none"]),
        "",
        f"### Next Suggested Action\n- {redact_secrets(summary.next_action, enabled=True)}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def update_dashboard(
    config: AppConfig,
    manifest: ManifestStore,
    summary: PipelineSummary,
    *,
    path_prefixes: list[str] | tuple[str, ...] | None = None,
) -> Path | None:
    dashboard_path = config.dashboard_path
    if dashboard_path is None:
        return None
    existing = dashboard_path.read_text(encoding="utf-8") if dashboard_path.exists() else ""
    replacement = render_dashboard_section(
        config,
        manifest,
        summary,
        path_prefixes=path_prefixes,
    )
    updated = _replace_marker_section(
        existing,
        start_marker=config.dashboard.auto_section_start,
        end_marker=config.dashboard.auto_section_end,
        replacement_body=replacement,
    )
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(updated, encoding="utf-8")
    return dashboard_path


def summarize_next_action(summary: PipelineSummary, *, approved_count: int = 0) -> str:
    if summary.failed:
        return "Check failed indexing items and rerun with --failed-only."
    if approved_count:
        return "Apply approved proposals, then reindex changed notes."
    if summary.proposal_candidates and not summary.write:
        return "Review dry-run candidates, then rerun with --write if safe."
    if summary.proposals_created:
        return "Review generated proposals and mark approved items."
    return "No immediate action."


def load_dashboard_document(config: AppConfig) -> str:
    dashboard_path = config.dashboard_path
    if dashboard_path is None or not dashboard_path.exists():
        return ""
    return load_markdown(dashboard_path, config.vault_path).text
