import pytest
import httpx
from pipeline.resources.llm import UnifiedLLMResource


class DummyResponse:
    def __init__(self, data: dict) -> None:
        self._data = data

    def json(self) -> dict:
        return self._data


class DummyAsyncClient:
    def __init__(self) -> None:
        self.is_closed = False
        self.requests = []

    async def __aenter__(self) -> "DummyAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.is_closed = True

    async def post(self, url: str, json: dict | None = None):
        self.requests.append((url, json))
        return DummyResponse({"candidates": [{"content": {"parts": [{"text": "hi"}]}}]})


@pytest.mark.asyncio
async def test_client_closed_after_generate(monkeypatch):
    client = DummyAsyncClient()
    monkeypatch.setattr(httpx, "AsyncClient", lambda: client)
    llm = UnifiedLLMResource(
        {
            "provider": "gemini",
            "api_key": "key",
            "model": "gemini-pro",
            "base_url": "http://x",
        }
    )
    result = await llm.generate("hello")

    assert result == "hi"
    assert client.is_closed
    assert client.requests == [
        (
            "http://x/v1beta/models/gemini-pro:generateContent?key=key",
            {"contents": [{"parts": [{"text": "hello"}]}]},
        )
    ]
