from __future__ import annotations

import re
from dataclasses import dataclass

from .markdown_loader import MarkdownDocument


HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    text: str
    heading: str
    index: int


def _split_large_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        candidate = text[start:end]
        if end < len(text):
            paragraph_break = candidate.rfind("\n\n")
            if paragraph_break > chunk_size // 2:
                end = start + paragraph_break
                candidate = text[start:end]
        cleaned = candidate.strip()
        if cleaned:
            chunks.append(cleaned)
        if end >= len(text):
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks


def chunk_markdown(document: MarkdownDocument, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    body = document.body.strip()
    if not body:
        return []

    matches = list(HEADING_PATTERN.finditer(body))
    sections: list[tuple[str, str]] = []

    if not matches:
        sections.append(("Document", body))
    else:
        first_start = matches[0].start()
        preamble = body[:first_start].strip()
        if preamble:
            sections.append(("Document", preamble))

        for index, match in enumerate(matches):
            heading = match.group(2).strip()
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            sections.append((heading, body[start:end].strip()))

    chunks: list[TextChunk] = []
    chunk_index = 0
    for heading, section_text in sections:
        for part in _split_large_text(section_text, chunk_size, chunk_overlap):
            chunk_id = f"{document.file_hash[:12]}-{chunk_index}"
            chunks.append(TextChunk(chunk_id=chunk_id, text=part, heading=heading, index=chunk_index))
            chunk_index += 1
    return chunks
