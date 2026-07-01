from __future__ import annotations

import os
import time
from typing import Any

import requests

from .config import AppConfig


class NVIDIAClientError(RuntimeError):
    pass


class NVIDIAAPIKeyMissingError(NVIDIAClientError):
    pass


class NVIDIAClient:
    DEFAULT_EMBED_BATCH_SIZE = 1
    DEFAULT_RETRY_ATTEMPTS = 3
    DEFAULT_RETRY_BACKOFF_SECONDS = 2.0
    RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        *,
        base_url: str,
        llm_model: str,
        embedding_model: str,
        rerank_model: str = "",
        api_key: str | None = None,
        timeout_seconds: int = 60,
        batch_size: int | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
        max_input_chars: int | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.rerank_model = rerank_model.strip()
        self.api_key = self._resolve_api_key(api_key)
        self.timeout_seconds = timeout_seconds
        self.batch_size = batch_size or self.DEFAULT_EMBED_BATCH_SIZE
        self.max_retries = max_retries or self.DEFAULT_RETRY_ATTEMPTS
        self.retry_backoff_seconds = (
            retry_backoff_seconds
            if retry_backoff_seconds is not None
            else self.DEFAULT_RETRY_BACKOFF_SECONDS
        )
        self.max_input_chars = max_input_chars
        self.session = session or requests.Session()

    @classmethod
    def from_config(
        cls, config: AppConfig, *, api_key: str | None = None, session: requests.Session | None = None
    ) -> "NVIDIAClient":
        return cls(
            base_url=config.nvidia.base_url,
            llm_model=config.nvidia.llm_model,
            embedding_model=config.nvidia.embedding_model,
            rerank_model=config.nvidia.rerank_model,
            api_key=api_key,
            timeout_seconds=config.embedding.timeout_seconds,
            batch_size=config.embedding.batch_size,
            max_retries=config.embedding.max_retries,
            retry_backoff_seconds=config.embedding.retry_backoff_seconds,
            max_input_chars=config.embedding.max_chunk_chars,
            session=session,
        )

    @staticmethod
    def _resolve_api_key(api_key: str | None) -> str:
        resolved = api_key or os.getenv("NVIDIA_API_KEY")
        if not resolved:
            raise NVIDIAAPIKeyMissingError(
                "NVIDIA_API_KEY is not set. Export NVIDIA_API_KEY before using NVIDIA-backed commands."
            )
        return resolved

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: NVIDIAClientError | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    headers=self._headers(),
                    json=payload,
                    timeout=self.timeout_seconds,
                )
            except requests.RequestException as exc:
                last_error = NVIDIAClientError(f"NVIDIA API request failed: {exc}")
            else:
                if response.status_code in self.RETRY_STATUS_CODES:
                    last_error = NVIDIAClientError(
                        f"NVIDIA API returned HTTP {response.status_code}: {response.text[:500]}"
                    )
                elif response.status_code >= 400:
                    raise NVIDIAClientError(
                        f"NVIDIA API returned HTTP {response.status_code}: {response.text[:500]}"
                    )
                else:
                    try:
                        data = response.json()
                    except ValueError as exc:
                        raise NVIDIAClientError("NVIDIA API returned non-JSON response.") from exc

                    if not isinstance(data, dict):
                        raise NVIDIAClientError("NVIDIA API returned unexpected response payload.")
                    return data

            if attempt < self.max_retries:
                time.sleep(self.retry_backoff_seconds * (2 ** (attempt - 1)))

        assert last_error is not None
        raise last_error

    def chat_markdown(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1800,
    ) -> str:
        payload = {
            "model": self.llm_model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        data = self._post("/chat/completions", payload)
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise NVIDIAClientError("NVIDIA chat response was empty.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, list):
            parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            content = "".join(parts)
        if not isinstance(content, str) or not content.strip():
            raise NVIDIAClientError("NVIDIA chat response did not contain text content.")
        return content.strip()

    def _normalize_embedding_text(self, value: Any, *, index: int) -> str:
        if value is None:
            raise NVIDIAClientError(f"NVIDIA embedding input at index {index} was None.")
        if not isinstance(value, str):
            value = str(value)
        normalized = value.strip()
        if not normalized:
            raise NVIDIAClientError(f"NVIDIA embedding input at index {index} was empty.")
        if self.max_input_chars and len(normalized) > self.max_input_chars:
            normalized = normalized[: self.max_input_chars]
        return normalized

    def embed_texts(self, texts: list[str], *, input_type: str) -> list[list[float]]:
        if not texts:
            return []

        normalized_texts = [
            self._normalize_embedding_text(text, index=index)
            for index, text in enumerate(texts)
        ]

        embeddings: list[list[float]] = []
        for start in range(0, len(normalized_texts), self.batch_size):
            batch = normalized_texts[start : start + self.batch_size]
            payload = {
                "model": self.embedding_model,
                "input": batch,
                "input_type": input_type,
                "encoding_format": "float",
            }
            data = self._post("/embeddings", payload)
            rows = data.get("data")
            if not isinstance(rows, list) or not rows:
                raise NVIDIAClientError("NVIDIA embedding response was empty.")

            if len(rows) != len(batch):
                raise NVIDIAClientError("NVIDIA embedding response size did not match the request.")

            for row in rows:
                embedding = row.get("embedding") if isinstance(row, dict) else None
                if not isinstance(embedding, list):
                    raise NVIDIAClientError("NVIDIA embedding response contained invalid rows.")
                embeddings.append([float(value) for value in embedding])
        return embeddings

    def rerank(
        self, *, query: str, documents: list[str], top_k: int
    ) -> list[dict[str, float | int]]:
        if not self.rerank_model:
            return [{"index": index, "score": float(len(documents) - index)} for index in range(len(documents))]

        payload = {
            "model": self.rerank_model,
            "query": query,
            "documents": documents,
            "top_n": top_k,
        }
        data = self._post("/reranking", payload)
        results = data.get("results")
        if not isinstance(results, list):
            raise NVIDIAClientError("NVIDIA rerank response was empty.")

        normalized: list[dict[str, float | int]] = []
        for row in results[:top_k]:
            if not isinstance(row, dict):
                continue
            index = row.get("index")
            score = row.get("relevance_score", row.get("score", 0.0))
            if isinstance(index, int):
                normalized.append({"index": index, "score": float(score)})

        if not normalized:
            raise NVIDIAClientError("NVIDIA rerank response did not contain usable results.")
        return normalized
