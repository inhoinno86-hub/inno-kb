from __future__ import annotations

from dataclasses import dataclass

from .config import AppConfig
from .nvidia_client import NVIDIAClient
from .vector_store import ChromaVectorStore, SearchResult


DEFAULT_MAX_EVIDENCE_DISTANCE = 1.1


@dataclass(frozen=True)
class QAResult:
    answer: str
    sources: list[str]
    results: list[SearchResult]
    evidence: dict[str, str | int | float | bool | None]

    def to_markdown(self) -> str:
        lines = ["## Answer", "", self.answer, "", "## Sources", ""]
        if self.sources:
            lines.extend(self.sources)
        else:
            lines.append("* none")

        lines.extend(["", "## Evidence", ""])
        for key, value in self.evidence.items():
            if value is None:
                rendered = ""
            elif isinstance(value, bool):
                rendered = "true" if value else "false"
            else:
                rendered = str(value)
            lines.append(f"* {key}: {rendered}")
        return "\n".join(lines).rstrip()


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
    seen: set[str] = set()
    for result in results:
        source = str(result.metadata.get("source", "unknown"))
        heading = str(result.metadata.get("heading", "Document")) or "Document"
        label = f"{source} > {heading}"
        if label in seen:
            continue
        seen.add(label)
        formatted.append(f"{len(formatted) + 1}. {label}")
    return formatted


def _coerce_stores(
    store: ChromaVectorStore | list[ChromaVectorStore],
) -> list[ChromaVectorStore]:
    if isinstance(store, list):
        return store
    return [store]


def _merge_results(
    stores: list[ChromaVectorStore],
    *,
    embedding: list[float],
    top_k: int,
) -> list[SearchResult]:
    merged: list[SearchResult] = []
    for store in stores:
        merged.extend(store.query(embedding=embedding, top_k=top_k))
    merged.sort(key=lambda item: item.distance)
    return merged[:top_k]


def _is_sufficient_context(config: AppConfig, results: list[SearchResult]) -> tuple[bool, str]:
    if not results:
        return False, "insufficient_relevant_context"

    best_distance = results[0].distance
    max_distance = (
        config.rag.max_evidence_distance
        if config.rag.max_evidence_distance is not None
        else DEFAULT_MAX_EVIDENCE_DISTANCE
    )
    if max_distance is not None and best_distance > max_distance:
        return False, "insufficient_relevant_context"

    if config.rag.min_evidence_score is not None:
        best_score = max(0.0, 1.0 - best_distance)
        if best_score < config.rag.min_evidence_score:
            return False, "insufficient_relevant_context"

    return True, ""


def answer_question(
    config: AppConfig,
    client: NVIDIAClient,
    store: ChromaVectorStore | list[ChromaVectorStore],
    query: str,
) -> QAResult:
    stores = _coerce_stores(store)
    query_embedding = client.embed_texts(
        [query],
        input_type=config.embedding.query_input_type,
    )[0]
    results = _merge_results(stores, embedding=query_embedding, top_k=config.rag.top_k)
    sufficient, reason = _is_sufficient_context(config, results)
    if not sufficient:
        threshold = (
            config.rag.max_evidence_distance
            if config.rag.max_evidence_distance is not None
            else DEFAULT_MAX_EVIDENCE_DISTANCE
        )
        return QAResult(
            answer="근거 부족",
            sources=["* none"],
            results=[],
            evidence={
                "reason": reason,
                "top_k": config.rag.top_k,
                "threshold": threshold,
            },
        )

    rerank_used = False
    if config.nvidia.rerank_model:
        results = rerank_results(client, query, results, config.rag.rerank_top_k)
        rerank_used = True

    context_blocks = []
    for index, result in enumerate(results, start=1):
        source = result.metadata.get("source", "unknown")
        heading = result.metadata.get("heading", "Document")
        context_blocks.append(f"[{index}] source={source} heading={heading}\n{result.text}")

    system_prompt = (
        "You answer questions using only the supplied Obsidian context. "
        "If the supplied context is insufficient, respond exactly with '근거 부족'. "
        "Do not answer anything that is not present in the provided context. "
        "Do not invent facts."
    )
    user_prompt = (
        f"질문:\n{query}\n\n"
        f"근거 문맥:\n\n{'\n\n'.join(context_blocks)}\n\n"
        "제공된 context에 없는 내용은 답하지 말 것. 답변만 작성하라."
    )
    answer = client.chat_markdown(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=1200,
    )
    sources = format_sources(results)
    if config.rag.require_sources and not sources:
        return QAResult(
            answer="근거 부족",
            sources=["* none"],
            results=[],
            evidence={
                "reason": "insufficient_relevant_context",
                "top_k": config.rag.top_k,
                "threshold": config.rag.max_evidence_distance,
            },
        )

    collections = sorted(
        {
            value
            for result in results
            if result.metadata
            for value in [str(result.metadata.get("collection", "")).strip()]
            if value
        }
    )
    return QAResult(
        answer=answer.strip() or "근거 부족",
        sources=sources or ["* none"],
        results=results,
        evidence={
            "top_k": config.rag.top_k,
            "rerank_used": rerank_used,
            "collection": ", ".join(collections) if collections else config.rag.collection_name,
            "model": config.nvidia.llm_model,
        },
    )
