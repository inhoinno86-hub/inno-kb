from __future__ import annotations

import pytest

from inno_obsidian_ai.nvidia_client import (
    NVIDIAAPIKeyMissingError,
    NVIDIAClient,
    NVIDIAClientError,
)


def test_missing_api_key_has_clear_error(monkeypatch) -> None:
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    with pytest.raises(NVIDIAAPIKeyMissingError, match="NVIDIA_API_KEY is not set"):
        NVIDIAClient(
            base_url="https://integrate.api.nvidia.com/v1",
            llm_model="test",
            embedding_model="embed",
        )


def test_embed_texts_rejects_empty_input() -> None:
    client = NVIDIAClient(
        base_url="https://integrate.api.nvidia.com/v1",
        llm_model="test",
        embedding_model="embed",
        api_key="test-key",
    )
    with pytest.raises(NVIDIAClientError, match="was empty"):
        client.embed_texts(["   "], input_type="query")
