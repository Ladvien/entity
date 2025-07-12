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
