from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml
from yaml import YAMLError

from .config import ensure_within
from .safety import sha256_file


FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


@dataclass(frozen=True)
class MarkdownDocument:
    path: Path
    relative_path: str
    text: str
    body: str
    frontmatter: dict[str, Any]
    file_hash: str


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    normalized = text.lstrip("\ufeff")
    match = FRONTMATTER_PATTERN.match(normalized)
    if not match:
        return {}, normalized

    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except YAMLError:
        frontmatter = {}
    if not isinstance(frontmatter, dict):
        frontmatter = {}

    body = normalized[match.end() :]
    return frontmatter, body


def load_markdown(path: Path, vault_path: Path) -> MarkdownDocument:
    confined = ensure_within(vault_path, path)
    text = confined.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    return MarkdownDocument(
        path=confined,
        relative_path=confined.relative_to(vault_path).as_posix(),
        text=text,
        body=body,
        frontmatter=frontmatter,
        file_hash=sha256_file(confined),
    )


def iter_markdown_files(root: Path) -> Iterable[Path]:
    yield from sorted(root.rglob("*.md"))
