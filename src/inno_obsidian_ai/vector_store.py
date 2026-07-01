from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchResult:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float


class ChromaVectorStore:
    def __init__(self, *, persist_dir: str, collection_name: str) -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError(
                "chromadb is not installed. Install project dependencies before indexing."
            ) from exc

        client = chromadb.PersistentClient(path=persist_dir)
        self.collection = client.get_or_create_collection(name=collection_name)

    def delete_source(self, relative_path: str) -> None:
        self.collection.delete(where={"source": relative_path})

    def upsert(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def query(self, *, embedding: list[float], top_k: int) -> list[SearchResult]:
        response = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )
        ids = response.get("ids", [[]])[0]
        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]

        results: list[SearchResult] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            results.append(
                SearchResult(
                    chunk_id=str(chunk_id),
                    text=str(text),
                    metadata=dict(metadata or {}),
                    distance=float(distance),
                )
            )
        return results
