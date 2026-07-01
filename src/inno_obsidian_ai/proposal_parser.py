from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig
from .markdown_loader import load_markdown


SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
DESTINATION_PATTERN = re.compile(r'^\s*-\s+path:\s*"([^"]+)"\s*\|\s*reason:\s*"([^"]*)"\s*$', re.MULTILINE)


@dataclass(frozen=True)
class DestinationNote:
    relative_path: str
    reason: str


@dataclass(frozen=True)
class ProposalDocument:
    relative_path: str
    source_file: str
    project: str
    feature: str
    status: str
    created_at: str
    model: str
    source_hash: str
    pipeline_run_id: str
    redacted: bool
    sections: dict[str, str]
    destinations: list[DestinationNote]


def split_sections(body: str) -> dict[str, str]:
    matches = list(SECTION_PATTERN.finditer(body))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        title = match.group(1).strip()
        sections[title] = body[start:end].strip()
    return sections


def extract_destinations(section_text: str) -> list[DestinationNote]:
    return [
        DestinationNote(relative_path=match.group(1).strip(), reason=match.group(2).strip())
        for match in DESTINATION_PATTERN.finditer(section_text)
    ]


def load_proposal(config: AppConfig, proposal_path: Path) -> ProposalDocument:
    document = load_markdown(proposal_path, config.vault_path)
    frontmatter = document.frontmatter
    source_file = str(frontmatter.get("source_file") or "").strip()
    if not source_file:
        raise ValueError(f"Proposal missing source_file: {document.relative_path}")

    config.resolve_in_vault(source_file)
    sections = split_sections(document.body)
    return ProposalDocument(
        relative_path=document.relative_path,
        source_file=source_file,
        project=str(frontmatter.get("project") or "확인 필요"),
        feature=str(frontmatter.get("feature") or Path(source_file).stem),
        status=str(frontmatter.get("status") or "review"),
        created_at=str(frontmatter.get("created_at") or ""),
        model=str(frontmatter.get("model") or ""),
        source_hash=str(frontmatter.get("source_hash") or ""),
        pipeline_run_id=str(frontmatter.get("pipeline_run_id") or ""),
        redacted=bool(frontmatter.get("redacted", False)),
        sections=sections,
        destinations=extract_destinations(sections.get("Suggested Destination Notes", "")),
    )


def build_append_block(proposal: ProposalDocument) -> str:
    source_name = Path(proposal.source_file).name
    date_label = source_name.replace("working_list_", "").split("_", 3)
    if len(date_label) >= 3:
        heading_date = f"{date_label[0]}-{date_label[1]}-{date_label[2]}"
    else:
        heading_date = proposal.created_at[:10] or "unknown-date"

    heading = f"## {heading_date} - {proposal.feature}"
    sections_to_append = [
        "Summary",
        "Changed Files",
        "Commands",
        "Tests",
        "Decisions",
        "TODO",
        "Risks / Follow-up",
        "Uncertain Items",
    ]
    lines = [heading, "", f"- Source: `{proposal.source_file}`", f"- Proposal: `{proposal.relative_path}`", ""]
    for section_name in sections_to_append:
        content = proposal.sections.get(section_name, "").strip() or "확인 필요"
        lines.extend([f"### {section_name}", "", content, ""])
    return "\n".join(lines).rstrip() + "\n"
