from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from inno_obsidian_ai.manifest import ManifestStore


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "index_obsidian_vault.py"
SPEC = importlib.util.spec_from_file_location("index_obsidian_vault_script", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write_markdown(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class _FakeStore:
    instances: dict[str, "_FakeStore"] = {}
    history: list["_FakeStore"] = []

    def __init__(self, *, persist_dir: str, collection_name: str) -> None:
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.delete_calls: list[str] = []
        self.upsert_calls: list[dict[str, object]] = []
        _FakeStore.instances[collection_name] = self
        _FakeStore.history.append(self)

    def delete_source(self, relative_path: str) -> None:
        self.delete_calls.append(relative_path)

    def upsert(self, *, ids, documents, metadatas, embeddings) -> None:
        self.upsert_calls.append(
            {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
                "embeddings": embeddings,
            }
        )


class _FakeClient:
    instances: list["_FakeClient"] = []
    raise_on_embed: str | None = None

    def __init__(self) -> None:
        self.embed_calls: list[tuple[list[str], str]] = []
        _FakeClient.instances.append(self)

    @classmethod
    def from_config(cls, config):
        return cls()

    def embed_texts(self, texts, *, input_type):
        self.embed_calls.append((list(texts), input_type))
        if self.raise_on_embed:
            raise MODULE.NVIDIAClientError(self.raise_on_embed)
        return [[0.1, 0.2] for _ in texts]


def _patch_runtime(monkeypatch) -> None:
    _FakeStore.instances = {}
    _FakeStore.history = []
    _FakeClient.instances = []
    _FakeClient.raise_on_embed = None
    monkeypatch.setattr(MODULE, "ChromaVectorStore", _FakeStore)
    monkeypatch.setattr(MODULE, "NVIDIAClient", _FakeClient)


def test_should_index_excludes_raw_logs_and_review(config) -> None:
    assert MODULE.should_index(config, "00_Inbox/codex_logs/2026-07-01/a.md") is False
    assert MODULE.should_index(config, "00_Inbox/_review/2026-07-01/a.md") is False
    assert MODULE.should_index(config, "10_Projects/INNO_KIS_Trading/06_Logs/a.md") is True


def test_should_index_honors_path_prefix(config) -> None:
    assert (
        MODULE.should_index(
            config,
            "10_Projects/INNO_KIS_Trading/06_Logs/a.md",
            ["10_Projects/INNO_KIS_Trading/06_Logs"],
        )
        is True
    )
    assert (
        MODULE.should_index(
            config,
            "10_Projects/INNO_KIS_Trading/07_References/b.md",
            ["10_Projects/INNO_KIS_Trading/06_Logs"],
        )
        is False
    )


def test_index_script_skips_unchanged_files(monkeypatch, vault: Path, config_path: Path, capsys) -> None:
    _patch_runtime(monkeypatch)
    note = vault / "10_Projects" / "INNO_KIS_Trading" / "06_Logs" / "a.md"
    _write_markdown(note, "# Note\n\nhello\n")

    assert MODULE.main(["--config", str(config_path), "--write"]) == 0
    assert MODULE.main(["--config", str(config_path), "--write"]) == 0

    output = capsys.readouterr().out
    assert "SKIP 10_Projects/INNO_KIS_Trading/06_Logs/a.md (unchanged)" in output
    assert sum(len(store.upsert_calls) for store in _FakeStore.history) == 1


def test_index_script_reindexes_when_file_hash_changes(
    monkeypatch, vault: Path, config_path: Path
) -> None:
    _patch_runtime(monkeypatch)
    note = vault / "10_Projects" / "INNO_KIS_Trading" / "06_Logs" / "a.md"
    _write_markdown(note, "# Note\n\nhello\n")

    assert MODULE.main(["--config", str(config_path), "--write"]) == 0
    _write_markdown(note, "# Note\n\nhello changed\n")
    assert MODULE.main(["--config", str(config_path), "--write"]) == 0

    assert sum(len(store.upsert_calls) for store in _FakeStore.history) == 2
    assert (
        sum(store.delete_calls.count("10_Projects/INNO_KIS_Trading/06_Logs/a.md") for store in _FakeStore.history)
        == 2
    )


def test_index_script_reindexes_when_embedding_model_changes(
    monkeypatch, vault: Path, config_path: Path
) -> None:
    _patch_runtime(monkeypatch)
    note = vault / "10_Projects" / "INNO_KIS_Trading" / "06_Logs" / "a.md"
    _write_markdown(note, "# Note\n\nhello\n")

    assert MODULE.main(["--config", str(config_path), "--write"]) == 0
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace('embedding_model: "test-embed"', 'embedding_model: "test-embed-v2"'),
        encoding="utf-8",
    )
    assert MODULE.main(["--config", str(config_path), "--write"]) == 0

    assert sum(len(store.upsert_calls) for store in _FakeStore.history) == 2


def test_path_prefix_limits_scope(monkeypatch, vault: Path, config_path: Path, capsys) -> None:
    _patch_runtime(monkeypatch)
    note_a = vault / "10_Projects" / "INNO_KIS_Trading" / "06_Logs" / "a.md"
    note_b = vault / "10_Projects" / "INNO_KIS_Trading" / "07_References" / "b.md"
    _write_markdown(note_a, "# A\n\nhello\n")
    _write_markdown(note_b, "# B\n\nworld\n")

    assert (
        MODULE.main(
            [
                "--config",
                str(config_path),
                "--path-prefix",
                "10_Projects/INNO_KIS_Trading/06_Logs",
                "--dry-run",
                "--stats",
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "a.md" in output
    assert "b.md" not in output
    assert "estimated_chunks=" in output


def test_note_type_policy_selects_collection(monkeypatch, vault: Path, config_path: Path) -> None:
    _patch_runtime(monkeypatch)
    note = vault / "50_Decisions" / "decision.md"
    _write_markdown(note, "# Decision\n\napproved\n")

    assert MODULE.main(["--config", str(config_path), "--write"]) == 0

    assert "decisions" in _FakeStore.instances
    assert len(_FakeStore.instances["decisions"].upsert_calls) == 1


def test_cleanup_missing_dry_run_only_reports(monkeypatch, vault: Path, config_path: Path, capsys) -> None:
    _patch_runtime(monkeypatch)
    note = vault / "10_Projects" / "INNO_KIS_Trading" / "06_Logs" / "a.md"
    _write_markdown(note, "# Note\n\nhello\n")

    assert MODULE.main(["--config", str(config_path), "--write"]) == 0
    note.unlink()

    assert MODULE.main(["--config", str(config_path), "--cleanup-missing", "--dry-run"]) == 0

    output = capsys.readouterr().out
    assert "DRY-RUN cleanup 10_Projects/INNO_KIS_Trading/06_Logs/a.md" in output
    manifest = ManifestStore((vault / ".inno_rag" / "manifest.sqlite"))
    assert manifest.get_indexed_file("10_Projects/INNO_KIS_Trading/06_Logs/a.md") is not None


def test_cleanup_missing_executes_delete(monkeypatch, vault: Path, config_path: Path) -> None:
    _patch_runtime(monkeypatch)
    note = vault / "10_Projects" / "INNO_KIS_Trading" / "06_Logs" / "a.md"
    _write_markdown(note, "# Note\n\nhello\n")

    assert MODULE.main(["--config", str(config_path), "--write"]) == 0
    note.unlink()
    assert MODULE.main(["--config", str(config_path), "--cleanup-missing", "--write"]) == 0

    manifest = ManifestStore((vault / ".inno_rag" / "manifest.sqlite"))
    assert manifest.get_indexed_file("10_Projects/INNO_KIS_Trading/06_Logs/a.md") is None
    assert "10_Projects/INNO_KIS_Trading/06_Logs/a.md" in _FakeStore.instances["project_notes"].delete_calls


def test_failed_only_retries_failed_files(monkeypatch, vault: Path, config_path: Path, capsys) -> None:
    _patch_runtime(monkeypatch)
    good_note = vault / "10_Projects" / "INNO_KIS_Trading" / "06_Logs" / "good.md"
    bad_note = vault / "10_Projects" / "INNO_KIS_Trading" / "06_Logs" / "bad.md"
    _write_markdown(good_note, "# Good\n\nhello\n")
    _write_markdown(bad_note, "# Bad\n\nhello\n")

    manifest = ManifestStore((vault / ".inno_rag" / "manifest.sqlite"))
    manifest.mark_index_failed(
        vault_relative_path="10_Projects/INNO_KIS_Trading/06_Logs/bad.md",
        path_hash="path-hash",
        file_hash="old-hash",
        file_size=1,
        modified_time=1.0,
        note_type="development_log",
        project="INNO_KIS_Trading",
        source="10_Projects/INNO_KIS_Trading/06_Logs/bad.md",
        collection_name="project_notes",
        embedding_model="test-embed",
        last_error="boom",
    )

    assert MODULE.main(["--config", str(config_path), "--failed-only", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "bad.md" in output
    assert "good.md" not in output


def test_audit_log_redacts_sensitive_errors(monkeypatch, vault: Path, config_path: Path) -> None:
    _patch_runtime(monkeypatch)
    _FakeClient.raise_on_embed = "Authorization: Bearer supersecrettoken"
    note = vault / "10_Projects" / "INNO_KIS_Trading" / "06_Logs" / "a.md"
    _write_markdown(note, "# Note\n\nhello\n")

    assert MODULE.main(["--config", str(config_path), "--write"]) == 2

    logs = sorted((vault / ".inno_rag" / "logs").glob("index-*.jsonl"))
    assert logs
    content = logs[-1].read_text(encoding="utf-8")
    assert "supersecrettoken" not in content
    assert "[REDACTED]" in content
