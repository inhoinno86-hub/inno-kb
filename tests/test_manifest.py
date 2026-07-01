from __future__ import annotations

from inno_obsidian_ai.manifest import IndexedChunkRecord, IndexedFileRecord
from inno_obsidian_ai.manifest import ManifestStore


def test_manifest_prevents_duplicate_processing(config) -> None:
    manifest = ManifestStore(config.manifest_path)
    assert manifest.needs_processing("organize_source", "a.md", "hash-1") is True
    manifest.record("organize_source", "a.md", "hash-1")
    assert manifest.needs_processing("organize_source", "a.md", "hash-1") is False
    assert manifest.needs_processing("organize_source", "a.md", "hash-2") is True


def test_indexed_file_reindexes_on_model_change(config) -> None:
    manifest = ManifestStore(config.manifest_path)
    manifest.upsert_indexed_file(
        IndexedFileRecord(
            vault_relative_path="10_Projects/a.md",
            path_hash="path-hash",
            file_hash="file-hash",
            file_size=10,
            modified_time=1.0,
            note_type="development_log",
            project="INNO",
            source="10_Projects/a.md",
            indexed_at="2026-07-01T00:00:00+00:00",
            index_status="indexed",
            last_error="",
            collection_name="project_notes",
            embedding_model="embed-v1",
            chunk_count=1,
            payload={},
        ),
        chunks=[
            IndexedChunkRecord(
                chunk_id="chunk-1",
                vault_relative_path="10_Projects/a.md",
                heading="Document",
                chunk_index=0,
                chunk_hash="chunk-hash",
                content_hash="content-hash",
                metadata_hash="metadata-hash",
                embedding_model="embed-v1",
                collection_name="project_notes",
                indexed_at="2026-07-01T00:00:00+00:00",
            )
        ],
    )

    assert (
        manifest.should_reindex_file(
            "10_Projects/a.md",
            file_hash="file-hash",
            embedding_model="embed-v1",
            collection_name="project_notes",
        )
        == (False, "unchanged")
    )
    assert (
        manifest.should_reindex_file(
            "10_Projects/a.md",
            file_hash="file-hash",
            embedding_model="embed-v2",
            collection_name="project_notes",
        )
        == (True, "embedding_model_changed")
    )
