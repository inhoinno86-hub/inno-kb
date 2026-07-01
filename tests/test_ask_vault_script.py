from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from inno_obsidian_ai.rag import QAResult


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ask_vault.py"
SPEC = importlib.util.spec_from_file_location("ask_vault_script", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class _FakeClient:
    @classmethod
    def from_config(cls, config):
        return cls()


class _FakeStore:
    def __init__(self, *, persist_dir: str, collection_name: str) -> None:
        self.persist_dir = persist_dir
        self.collection_name = collection_name


def test_ask_vault_prints_sources(monkeypatch, config_path: Path, capsys) -> None:
    monkeypatch.setattr(MODULE, "NVIDIAClient", _FakeClient)
    monkeypatch.setattr(MODULE, "ChromaVectorStore", _FakeStore)
    monkeypatch.setattr(
        MODULE,
        "answer_question",
        lambda config, client, stores, query: QAResult(
            answer="답변",
            sources=["1. a.md > Heading"],
            results=[],
            evidence={"top_k": 4, "rerank_used": False, "collection": "general", "model": "test"},
        ),
    )

    assert MODULE.main(["--config", str(config_path), "question"]) == 0
    output = capsys.readouterr().out
    assert "## Answer" in output
    assert "## Sources" in output
    assert "1. a.md > Heading" in output


def test_ask_vault_prints_none_for_insufficient_context(monkeypatch, config_path: Path, capsys) -> None:
    monkeypatch.setattr(MODULE, "NVIDIAClient", _FakeClient)
    monkeypatch.setattr(MODULE, "ChromaVectorStore", _FakeStore)
    monkeypatch.setattr(
        MODULE,
        "answer_question",
        lambda config, client, stores, query: QAResult(
            answer="근거 부족",
            sources=["* none"],
            results=[],
            evidence={
                "reason": "insufficient_relevant_context",
                "top_k": 4,
                "threshold": 0.8,
            },
        ),
    )

    assert MODULE.main(["--config", str(config_path), "question"]) == 0
    output = capsys.readouterr().out
    assert "근거 부족" in output
    assert "* none" in output
