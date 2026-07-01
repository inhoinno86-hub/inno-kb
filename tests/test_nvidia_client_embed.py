from __future__ import annotations

from inno_obsidian_ai.nvidia_client import NVIDIAClient


class _FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload
        self.text = ""

    def json(self):
        return self._payload


class _FakeSession:
    def __init__(self):
        self.last_json = None
        self.payloads = []

    def post(self, url, headers, json, timeout):
        self.last_json = json
        self.payloads.append(json)
        return _FakeResponse(
            {"data": [{"embedding": [0.1, 0.2]} for _ in json["input"]]}
        )


def test_embed_texts_sends_input_type() -> None:
    session = _FakeSession()
    client = NVIDIAClient(
        base_url="https://integrate.api.nvidia.com/v1",
        llm_model="test-llm",
        embedding_model="test-embed",
        api_key="test-key",
        session=session,
    )

    embeddings = client.embed_texts(["hello"], input_type="query")

    assert embeddings == [[0.1, 0.2]]
    assert session.last_json["input_type"] == "query"


def test_embed_texts_batches_large_requests() -> None:
    session = _FakeSession()
    client = NVIDIAClient(
        base_url="https://integrate.api.nvidia.com/v1",
        llm_model="test-llm",
        embedding_model="test-embed",
        api_key="test-key",
        session=session,
    )

    embeddings = client.embed_texts(["x"] * 17, input_type="passage")

    assert len(embeddings) == 17
    assert len(session.payloads) == 17
    assert all(len(payload["input"]) == 1 for payload in session.payloads)
