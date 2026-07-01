from __future__ import annotations

import hashlib
import re
from pathlib import Path


SECRET_KEY_PATTERN = re.compile(
    r"(?im)^([^\n#]*?(?:api[_-]?key|token|password|passwd|secret|authorization)\s*[:=]\s*)(.+)$"
)
BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-+/=]+")
LONG_TOKEN_PATTERN = re.compile(r"\b[A-Za-z0-9_\-]{24,}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
ACCOUNT_NUMBER_PATTERN = re.compile(r"\b\d{9,18}\b")


def _looks_like_secret_token(token: str) -> bool:
    if len(token) < 24:
        return False

    has_alpha = any(char.isalpha() for char in token)
    has_digit = any(char.isdigit() for char in token)
    has_upper = any(char.isupper() for char in token)
    has_lower = any(char.islower() for char in token)
    has_separator = any(char in "-_" for char in token)

    if has_alpha and has_digit:
        return True
    if has_upper and has_lower and has_separator:
        return True
    return False


def redact_secrets(text: str, enabled: bool = True) -> str:
    if not enabled or not text:
        return text

    redacted = SECRET_KEY_PATTERN.sub(r"\1[REDACTED]", text)
    redacted = BEARER_PATTERN.sub("Bearer [REDACTED]", redacted)
    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", redacted)
    redacted = ACCOUNT_NUMBER_PATTERN.sub("[REDACTED_NUMBER]", redacted)

    lines: list[str] = []
    for line in redacted.splitlines():
        if len(line) > 4096:
            lines.append(line)
            continue
        lines.append(
            LONG_TOKEN_PATTERN.sub(
                lambda match: "[REDACTED_TOKEN]"
                if _looks_like_secret_token(match.group(0))
                else match.group(0),
                line,
            )
        )
    return "\n".join(lines)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
