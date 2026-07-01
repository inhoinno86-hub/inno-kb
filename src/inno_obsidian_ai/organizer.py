from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import AppConfig
from .manifest import ManifestStore
from .markdown_loader import load_markdown
from .nvidia_client import NVIDIAClient
from .safety import redact_secrets


PROJECT_PATTERN = re.compile(r"(?im)^(?:project|프로젝트)\s*:\s*(.+)$")


@dataclass(frozen=True)
class OrganizationResult:
    source_file: str
    proposal_file: str
    file_hash: str
    skipped: bool
    reason: str


def detect_feature_name(relative_path: str) -> str:
    stem = Path(relative_path).stem
    match = re.match(r"working_list_\d{4}_\d{2}_\d{2}_(.+)", stem)
    if match:
        return match.group(1)
    return stem


def detect_project_name(text: str) -> str:
    match = PROJECT_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return "확인 필요"


def build_organization_prompt(source_file: str, project: str, feature: str, content: str) -> tuple[str, str]:
    system_prompt = (
        "You organize Codex work logs into Obsidian-ready Markdown. "
        "Use only facts present in the source. Never invent file names, commands, tests, decisions, or outcomes. "
        "When information cannot be verified from the source, write '확인 필요'. "
        "Keep output in Korean where possible. Output Markdown sections only."
    )
    user_prompt = f"""
원본 source_file: {source_file}
프로젝트 추정값: {project}
feature 추정값: {feature}

아래 원본 로그를 기준으로 Obsidian 정리 제안 본문을 작성하라.

출력 규칙:
- 반드시 아래 섹션 순서를 지킨다.
- 원문에 없는 사실은 만들지 않는다.
- 확인 불가한 내용은 '확인 필요'로 쓴다.
- Suggested Destination Notes 섹션의 각 항목은 정확히 다음 형식의 bullet로 쓴다.
  - path: "상대경로.md" | reason: "이유"
- Suggested Obsidian Links 섹션은 wiki link 형식 [[...]] 또는 '확인 필요'를 사용한다.
- Human Review Required 섹션에는 승인 전에 사람이 확인할 사항을 bullet로 정리한다.

# Organization Proposal

## Summary

## Changed Files

## Commands

## Tests

## Decisions

## TODO

## Risks / Follow-up

## Suggested Destination Notes

## Suggested Obsidian Links

## Uncertain Items

## Human Review Required

원본 로그:
```markdown
{content}
```
""".strip()
    return system_prompt, user_prompt


def build_proposal_markdown(
    *,
    source_file: str,
    project: str,
    feature: str,
    model_name: str,
    created_at: str,
    proposal_body: str,
    source_hash: str,
) -> str:
    frontmatter = "\n".join(
        [
            "---",
            "type: llm_organization_proposal",
            f'source_file: "{source_file}"',
            f'project: "{project}"',
            f'feature: "{feature}"',
            'status: "review"',
            f'created_at: "{created_at}"',
            f'model: "{model_name}"',
            f'source_hash: "{source_hash}"',
            "---",
            "",
        ]
    )
    return f"{frontmatter}{proposal_body.strip()}\n"


def proposal_output_path(config: AppConfig, source_relative_path: str, file_hash: str) -> Path:
    source_path = Path(source_relative_path)
    date_segment = source_path.parent.name
    stem = source_path.stem
    filename = f"{stem}--{file_hash[:8]}.proposal.md"
    return config.review_dir / date_segment / filename


def organize_codex_logs(
    config: AppConfig,
    client: NVIDIAClient | None,
    manifest: ManifestStore,
    *,
    dry_run: bool | None = None,
) -> list[OrganizationResult]:
    effective_dry_run = config.safety.dry_run if dry_run is None else dry_run
    results: list[OrganizationResult] = []

    for markdown_path in sorted(config.codex_logs_dir.rglob("*.md")):
        document = load_markdown(markdown_path, config.vault_path)
        if not manifest.needs_processing("organize_source", document.relative_path, document.file_hash):
            results.append(
                OrganizationResult(
                    source_file=document.relative_path,
                    proposal_file="",
                    file_hash=document.file_hash,
                    skipped=True,
                    reason="unchanged",
                )
            )
            continue

        feature = detect_feature_name(document.relative_path)
        project = str(document.frontmatter.get("project") or detect_project_name(document.text))
        proposal_path = proposal_output_path(config, document.relative_path, document.file_hash)
        proposal_relative = config.to_vault_relative(proposal_path)

        if effective_dry_run:
            proposal_text = ""
        else:
            if client is None:
                raise ValueError("NVIDIA client is required when dry_run is disabled.")
            redacted_content = redact_secrets(document.text, enabled=config.safety.redact_secrets)
            system_prompt, user_prompt = build_organization_prompt(
                document.relative_path, project, feature, redacted_content
            )
            proposal_body = client.chat_markdown(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            created_at = datetime.now().astimezone().isoformat(timespec="seconds")
            proposal_text = build_proposal_markdown(
                source_file=document.relative_path,
                project=project,
                feature=feature,
                model_name=config.nvidia.llm_model,
                created_at=created_at,
                proposal_body=proposal_body,
                source_hash=document.file_hash,
            )

        if proposal_text:
            proposal_path.parent.mkdir(parents=True, exist_ok=True)
            proposal_path.write_text(proposal_text, encoding="utf-8")
            manifest.record(
                "organize_source",
                document.relative_path,
                document.file_hash,
                payload={"proposal_file": proposal_relative},
            )

        results.append(
            OrganizationResult(
                source_file=document.relative_path,
                proposal_file=proposal_relative,
                file_hash=document.file_hash,
                skipped=False,
                reason="dry-run" if effective_dry_run else "created",
            )
        )

    return results
