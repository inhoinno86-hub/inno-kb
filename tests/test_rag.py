from __future__ import annotations

from inno_obsidian_ai.rag import answer_question
from inno_obsidian_ai.vector_store import SearchResult


class _FakeClient:
    def embed_texts(self, texts, *, input_type):
        return [[0.1, 0.2]]

    def chat_markdown(self, **kwargs):
        return "answer"


class _FakeStore:
    def __init__(self, results):
        self._results = results

    def query(self, *, embedding, top_k):
        return self._results


def test_answer_question_returns_insufficient_when_distance_is_high(config) -> None:
    results = [
        SearchResult(
            chunk_id="1",
            text="irrelevant",
            metadata={"source": "a.md", "heading": "Document"},
            distance=1.3,
        )
    ]

    qa = answer_question(config, _FakeClient(), _FakeStore(results), "question")

    assert qa.answer == "근거 부족"
    assert qa.sources == ["- none"]


def test_answer_question_returns_answer_when_distance_is_good(config) -> None:
    results = [
        SearchResult(
            chunk_id="1",
            text="relevant",
            metadata={"source": "a.md", "heading": "Document"},
            distance=0.7,
        )
    ]

    qa = answer_question(config, _FakeClient(), _FakeStore(results), "question")

    assert qa.answer == "answer"
    assert qa.sources == ["- a.md :: Document"]
