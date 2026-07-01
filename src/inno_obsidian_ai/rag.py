from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .nvidia_client import NVIDIAClient
from .vector_store import ChromaVectorStore, SearchResult


MAX_EVIDENCE_DISTANCE = 1.1


@dataclass(frozen=True)
class QAResult:
    answer: str
    sources: list[str]
    results: list[SearchResult]


def rerank_results(
    client: NVIDIAClient,
    query: str,
    results: list[SearchResult],
    top_k: int,
) -> list[SearchResult]:
    if not results:
        return []

    ranked = client.rerank(
        query=query,
        documents=[result.text for result in results],
        top_k=min(top_k, len(results)),
    )
    reranked: list[SearchResult] = []
    for row in ranked:
        reranked.append(results[int(row["index"])])
    return reranked


def format_sources(results: list[SearchResult]) -> list[str]:
    formatted: list[str] = []
    for result in results:
        source = str(result.metadata.get("source", "unknown"))
        heading = str(result.metadata.get("heading", "Document"))
        formatted.append(f"- {source} :: {heading}")
    return formatted


def answer_question(
    config: AppConfig,
    client: NVIDIAClient,
    store: ChromaVectorStore,
    query: str,
) -> QAResult:
    query_embedding = client.embed_texts([query], input_type="query")[0]
    results = store.query(embedding=query_embedding, top_k=config.rag.top_k)
    if not results or results[0].distance > MAX_EVIDENCE_DISTANCE:
        return QAResult(answer="근거 부족", sources=["- none"], results=[])
    if config.nvidia.rerank_model:
        results = rerank_results(client, query, results, config.rag.rerank_top_k)

    context_blocks = []
    for index, result in enumerate(results, start=1):
        source = result.metadata.get("source", "unknown")
        heading = result.metadata.get("heading", "Document")
        context_blocks.append(
            f"[{index}] source={source} heading={heading}\n{result.text}"
        )

    system_prompt = (
        "You answer questions using only the supplied Obsidian context. "
        "If evidence is insufficient, respond exactly with '근거 부족'. "
        "Do not invent facts."
    )
    user_prompt = (
        f"질문:\n{query}\n\n"
        f"근거 문맥:\n\n" + "\n\n".join(context_blocks) + "\n\n답변만 작성하라."
    )
    answer = client.chat_markdown(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=1200)
    return QAResult(answer=answer, sources=format_sources(results), results=results)
