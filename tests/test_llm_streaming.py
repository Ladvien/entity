import httpx
import pytest


class OpenAIProvider:
    """Very small subset of the real provider used in tests."""

    def __init__(self, config: dict) -> None:
        self._base_url = config["base_url"].rstrip("/")
        self._model = config["model"]
        self._api_key = config["api_key"]
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "OpenAIProvider":
        self._client = httpx.AsyncClient()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def stream(self, prompt: str):
        if self._client is None:
            async with httpx.AsyncClient() as client:
                async for chunk in dummy_stream(client, "POST", self._base_url):
                    yield chunk
            return

        async for chunk in dummy_stream(self._client, "POST", self._base_url):
            yield chunk


class DummyStreamResponse:
    def __init__(self, lines):
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def raise_for_status(self) -> None:
        pass

    async def aiter_lines(self):
        for line in self._lines:
            yield line


def dummy_stream(self, method, url, json=None, headers=None, params=None):
    return DummyStreamResponse(
        ['data: {"choices": [{"delta": {"content": "hi"}}]}', "[DONE]"]
    )


@pytest.mark.asyncio
async def test_client_closed_after_stream_context_manager(monkeypatch):
    provider = OpenAIProvider({"base_url": "http://x", "model": "gpt", "api_key": "k"})
    monkeypatch.setattr(httpx.AsyncClient, "stream", dummy_stream)
    async with provider:
        chunks = [chunk async for chunk in provider.stream("test")]
        assert chunks == ["hi"]
        assert provider._client is not None
        assert not provider._client.is_closed
    assert provider._client is None


@pytest.mark.asyncio
async def test_client_closed_after_stream_no_context(monkeypatch):
    provider = OpenAIProvider({"base_url": "http://x", "model": "gpt", "api_key": "k"})
    monkeypatch.setattr(httpx.AsyncClient, "stream", dummy_stream)
    chunks = [chunk async for chunk in provider.stream("test")]
    assert chunks == ["hi"]
    assert provider._client is None
