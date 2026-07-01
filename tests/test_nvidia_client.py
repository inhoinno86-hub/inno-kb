from __future__ import annotations

import pytest

from inno_obsidian_ai.nvidia_client import NVIDIAAPIKeyMissingError, NVIDIAClient


def test_missing_api_key_has_clear_error(monkeypatch) -> None:
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    with pytest.raises(NVIDIAAPIKeyMissingError, match="NVIDIA_API_KEY is not set"):
        NVIDIAClient(
            base_url="https://integrate.api.nvidia.com/v1",
            llm_model="test",
            embedding_model="embed",
        )
