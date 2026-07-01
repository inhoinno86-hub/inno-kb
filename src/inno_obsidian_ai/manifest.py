from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


@dataclass(frozen=True)
class ManifestRecord:
    scope: str
    relative_path: str
    file_hash: str
    status: str
    payload: dict[str, Any]
    updated_at: str


class ManifestStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path)
        try:
            connection.row_factory = sqlite3.Row
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS manifest_entries (
                    scope TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (scope, relative_path)
                )
                """
            )

    def get(self, scope: str, relative_path: str) -> ManifestRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT scope, relative_path, file_hash, status, payload_json, updated_at
                FROM manifest_entries
                WHERE scope = ? AND relative_path = ?
                """,
                (scope, relative_path),
            ).fetchone()

        if row is None:
            return None

        return ManifestRecord(
            scope=row["scope"],
            relative_path=row["relative_path"],
            file_hash=row["file_hash"],
            status=row["status"],
            payload=json.loads(row["payload_json"] or "{}"),
            updated_at=row["updated_at"],
        )

    def needs_processing(self, scope: str, relative_path: str, file_hash: str) -> bool:
        record = self.get(scope, relative_path)
        return record is None or record.file_hash != file_hash

    def record(
        self,
        scope: str,
        relative_path: str,
        file_hash: str,
        *,
        status: str = "processed",
        payload: dict[str, Any] | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO manifest_entries (
                    scope, relative_path, file_hash, status, payload_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(scope, relative_path) DO UPDATE SET
                    file_hash = excluded.file_hash,
                    status = excluded.status,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (scope, relative_path, file_hash, status, payload_json, now),
            )
