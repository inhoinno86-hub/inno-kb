from __future__ import annotations

from pathlib import Path

from inno_obsidian_ai.chunker import chunk_markdown
from inno_obsidian_ai.markdown_loader import MarkdownDocument


def test_chunker_splits_by_heading() -> None:
    document = MarkdownDocument(
        path=Path("/tmp/test.md"),
        relative_path="test.md",
        text="# One\nBody\n\n## Two\nMore body",
        body="# One\nBody\n\n## Two\nMore body",
        frontmatter={},
        file_hash="abc123",
    )
    chunks = chunk_markdown(document, chunk_size=50, chunk_overlap=10)
    assert len(chunks) == 2
    assert chunks[0].heading == "One"
    assert chunks[1].heading == "Two"
