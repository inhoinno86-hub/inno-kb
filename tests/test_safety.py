from __future__ import annotations

from inno_obsidian_ai.safety import redact_secrets


def test_secret_redaction_masks_sensitive_tokens() -> None:
    text = "\n".join(
        [
            "api_key=abcd1234secret",
            "Authorization: Bearer supersecrettoken",
            "email: user@example.com",
            "account: 123456789012",
        ]
    )
    redacted = redact_secrets(text)
    assert "abcd1234secret" not in redacted
    assert "supersecrettoken" not in redacted
    assert "user@example.com" not in redacted
    assert "123456789012" not in redacted


def test_secret_redaction_preserves_long_snake_case_identifiers() -> None:
    text = "python scripts/organize_codex_inbox_with_nvidia.py --config config/obsidian_ai.yaml"
    redacted = redact_secrets(text)
    assert "organize_codex_inbox_with_nvidia.py" in redacted
