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


@dataclass(frozen=True)
class IndexedFileRecord:
    vault_relative_path: str
    path_hash: str
    file_hash: str
    file_size: int
    modified_time: float
    note_type: str
    project: str
    source: str
    indexed_at: str
    index_status: str
    last_error: str
    collection_name: str
    embedding_model: str
    chunk_count: int
    payload: dict[str, Any]


@dataclass(frozen=True)
class IndexedChunkRecord:
    chunk_id: str
    vault_relative_path: str
    heading: str
    chunk_index: int
    chunk_hash: str
    content_hash: str
    metadata_hash: str
    embedding_model: str
    collection_name: str
    indexed_at: str


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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS indexed_files (
                    vault_relative_path TEXT PRIMARY KEY,
                    path_hash TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    modified_time REAL NOT NULL,
                    note_type TEXT NOT NULL,
                    project TEXT NOT NULL,
                    source TEXT NOT NULL,
                    indexed_at TEXT NOT NULL,
                    index_status TEXT NOT NULL,
                    last_error TEXT NOT NULL DEFAULT '',
                    collection_name TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    payload_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS indexed_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    vault_relative_path TEXT NOT NULL,
                    heading TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_hash TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    metadata_hash TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    collection_name TEXT NOT NULL,
                    indexed_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_indexed_chunks_identity
                ON indexed_chunks (
                    vault_relative_path,
                    chunk_hash,
                    embedding_model,
                    collection_name
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_indexed_files_status
                ON indexed_files (index_status)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_indexed_files_collection
                ON indexed_files (collection_name)
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _json_dumps(payload: dict[str, Any] | None) -> str:
        return json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _row_to_manifest_record(row: sqlite3.Row) -> ManifestRecord:
        return ManifestRecord(
            scope=row["scope"],
            relative_path=row["relative_path"],
            file_hash=row["file_hash"],
            status=row["status"],
            payload=json.loads(row["payload_json"] or "{}"),
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_indexed_file_record(row: sqlite3.Row) -> IndexedFileRecord:
        return IndexedFileRecord(
            vault_relative_path=row["vault_relative_path"],
            path_hash=row["path_hash"],
            file_hash=row["file_hash"],
            file_size=int(row["file_size"]),
            modified_time=float(row["modified_time"]),
            note_type=row["note_type"],
            project=row["project"],
            source=row["source"],
            indexed_at=row["indexed_at"],
            index_status=row["index_status"],
            last_error=row["last_error"] or "",
            collection_name=row["collection_name"],
            embedding_model=row["embedding_model"],
            chunk_count=int(row["chunk_count"]),
            payload=json.loads(row["payload_json"] or "{}"),
        )

    @staticmethod
    def _row_to_indexed_chunk_record(row: sqlite3.Row) -> IndexedChunkRecord:
        return IndexedChunkRecord(
            chunk_id=row["chunk_id"],
            vault_relative_path=row["vault_relative_path"],
            heading=row["heading"],
            chunk_index=int(row["chunk_index"]),
            chunk_hash=row["chunk_hash"],
            content_hash=row["content_hash"],
            metadata_hash=row["metadata_hash"],
            embedding_model=row["embedding_model"],
            collection_name=row["collection_name"],
            indexed_at=row["indexed_at"],
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
        return self._row_to_manifest_record(row)

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
        now = self._now()
        payload_json = self._json_dumps(payload)
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

    def get_indexed_file(self, vault_relative_path: str) -> IndexedFileRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    vault_relative_path,
                    path_hash,
                    file_hash,
                    file_size,
                    modified_time,
                    note_type,
                    project,
                    source,
                    indexed_at,
                    index_status,
                    last_error,
                    collection_name,
                    embedding_model,
                    chunk_count,
                    payload_json
                FROM indexed_files
                WHERE vault_relative_path = ?
                """,
                (vault_relative_path,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_indexed_file_record(row)

    def list_indexed_files(
        self,
        *,
        path_prefixes: list[str] | tuple[str, ...] | None = None,
        collection_name: str | None = None,
        index_status: str | None = None,
    ) -> list[IndexedFileRecord]:
        conditions: list[str] = []
        parameters: list[Any] = []
        if collection_name:
            conditions.append("collection_name = ?")
            parameters.append(collection_name)
        if index_status:
            conditions.append("index_status = ?")
            parameters.append(index_status)

        sql = """
            SELECT
                vault_relative_path,
                path_hash,
                file_hash,
                file_size,
                modified_time,
                note_type,
                project,
                source,
                indexed_at,
                index_status,
                last_error,
                collection_name,
                embedding_model,
                chunk_count,
                payload_json
            FROM indexed_files
        """
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY vault_relative_path"

        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()

        records = [self._row_to_indexed_file_record(row) for row in rows]
        if not path_prefixes:
            return records

        prefixes = tuple(path_prefixes)
        return [
            record
            for record in records
            if any(
                record.vault_relative_path == prefix
                or record.vault_relative_path.startswith(f"{prefix}/")
                for prefix in prefixes
            )
        ]

    def list_chunks_for_file(self, vault_relative_path: str) -> list[IndexedChunkRecord]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    chunk_id,
                    vault_relative_path,
                    heading,
                    chunk_index,
                    chunk_hash,
                    content_hash,
                    metadata_hash,
                    embedding_model,
                    collection_name,
                    indexed_at
                FROM indexed_chunks
                WHERE vault_relative_path = ?
                ORDER BY chunk_index
                """,
                (vault_relative_path,),
            ).fetchall()
        return [self._row_to_indexed_chunk_record(row) for row in rows]

    def should_reindex_file(
        self,
        vault_relative_path: str,
        *,
        file_hash: str,
        embedding_model: str,
        collection_name: str,
        force: bool = False,
    ) -> tuple[bool, str]:
        if force:
            return True, "force"

        record = self.get_indexed_file(vault_relative_path)
        if record is None:
            return True, "new"
        if record.index_status == "failed":
            return True, "failed_retry"
        if record.file_hash != file_hash:
            return True, "file_hash_changed"
        if record.embedding_model != embedding_model:
            return True, "embedding_model_changed"
        if record.collection_name != collection_name:
            return True, "collection_changed"
        return False, "unchanged"

    def upsert_indexed_file(
        self,
        record: IndexedFileRecord,
        *,
        chunks: list[IndexedChunkRecord],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO indexed_files (
                    vault_relative_path,
                    path_hash,
                    file_hash,
                    file_size,
                    modified_time,
                    note_type,
                    project,
                    source,
                    indexed_at,
                    index_status,
                    last_error,
                    collection_name,
                    embedding_model,
                    chunk_count,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(vault_relative_path) DO UPDATE SET
                    path_hash = excluded.path_hash,
                    file_hash = excluded.file_hash,
                    file_size = excluded.file_size,
                    modified_time = excluded.modified_time,
                    note_type = excluded.note_type,
                    project = excluded.project,
                    source = excluded.source,
                    indexed_at = excluded.indexed_at,
                    index_status = excluded.index_status,
                    last_error = excluded.last_error,
                    collection_name = excluded.collection_name,
                    embedding_model = excluded.embedding_model,
                    chunk_count = excluded.chunk_count,
                    payload_json = excluded.payload_json
                """,
                (
                    record.vault_relative_path,
                    record.path_hash,
                    record.file_hash,
                    record.file_size,
                    record.modified_time,
                    record.note_type,
                    record.project,
                    record.source,
                    record.indexed_at,
                    record.index_status,
                    record.last_error,
                    record.collection_name,
                    record.embedding_model,
                    record.chunk_count,
                    self._json_dumps(record.payload),
                ),
            )
            connection.execute(
                "DELETE FROM indexed_chunks WHERE vault_relative_path = ?",
                (record.vault_relative_path,),
            )
            if chunks:
                connection.executemany(
                    """
                    INSERT INTO indexed_chunks (
                        chunk_id,
                        vault_relative_path,
                        heading,
                        chunk_index,
                        chunk_hash,
                        content_hash,
                        metadata_hash,
                        embedding_model,
                        collection_name,
                        indexed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            chunk.chunk_id,
                            chunk.vault_relative_path,
                            chunk.heading,
                            chunk.chunk_index,
                            chunk.chunk_hash,
                            chunk.content_hash,
                            chunk.metadata_hash,
                            chunk.embedding_model,
                            chunk.collection_name,
                            chunk.indexed_at,
                        )
                        for chunk in chunks
                    ],
                )

    def mark_index_failed(
        self,
        *,
        vault_relative_path: str,
        path_hash: str,
        file_hash: str,
        file_size: int,
        modified_time: float,
        note_type: str,
        project: str,
        source: str,
        collection_name: str,
        embedding_model: str,
        last_error: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.upsert_indexed_file(
            IndexedFileRecord(
                vault_relative_path=vault_relative_path,
                path_hash=path_hash,
                file_hash=file_hash,
                file_size=file_size,
                modified_time=modified_time,
                note_type=note_type,
                project=project,
                source=source,
                indexed_at=self._now(),
                index_status="failed",
                last_error=last_error,
                collection_name=collection_name,
                embedding_model=embedding_model,
                chunk_count=0,
                payload=payload or {},
            ),
            chunks=[],
        )

    def delete_indexed_file(self, vault_relative_path: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM indexed_chunks WHERE vault_relative_path = ?",
                (vault_relative_path,),
            )
            connection.execute(
                "DELETE FROM indexed_files WHERE vault_relative_path = ?",
                (vault_relative_path,),
            )
