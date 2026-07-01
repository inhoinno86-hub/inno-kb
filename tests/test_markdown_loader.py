from __future__ import annotations

from inno_obsidian_ai.markdown_loader import parse_frontmatter


def test_parse_frontmatter_tolerates_invalid_yaml() -> None:
    text = "---\ntype: note\n{{ card_data }}\n---\n\n# Body\n"
    frontmatter, body = parse_frontmatter(text)
    assert frontmatter == {}
    assert body.strip() == "# Body"
