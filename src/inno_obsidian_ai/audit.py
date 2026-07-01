from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .safety import redact_secrets


class AuditLogger:
    def __init__(self, log_dir: Path) -> None:
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
        self.log_path = self.log_dir / f"index-{timestamp}.jsonl"

    def log(
        self,
        *,
        action: str,
        vault_relative_path: str,
        status: str,
        file_hash: str = "",
        chunk_count: int = 0,
        collection: str = "",
        model: str = "",
        error: str = "",
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "vault_relative_path": vault_relative_path,
            "status": status,
            "file_hash": file_hash,
            "chunk_count": chunk_count,
            "collection": collection,
            "model": model,
            "error": redact_secrets(error, enabled=True),
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
