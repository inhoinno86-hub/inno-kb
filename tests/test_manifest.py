from __future__ import annotations

from inno_obsidian_ai.manifest import ManifestStore


def test_manifest_prevents_duplicate_processing(config) -> None:
    manifest = ManifestStore(config.manifest_path)
    assert manifest.needs_processing("organize_source", "a.md", "hash-1") is True
    manifest.record("organize_source", "a.md", "hash-1")
    assert manifest.needs_processing("organize_source", "a.md", "hash-1") is False
    assert manifest.needs_processing("organize_source", "a.md", "hash-2") is True
