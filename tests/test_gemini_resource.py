import asyncio
from unittest.mock import AsyncMock, patch

from pipeline.plugins.resources.gemini import GeminiResource


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - stub
        pass

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": "hi"}]}}]}


async def run_generate():
    resource = GeminiResource(
        {
            "api_key": "key",
            "model": "gemini-pro",
            "base_url": "https://generativelanguage.googleapis.com",
        }
    )
    with patch(
        "httpx.AsyncClient.post", new=AsyncMock(return_value=FakeResponse())
    ) as mock_post:
        result = await resource.generate("hello")
        mock_post.assert_awaited_with(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            headers={"Content-Type": "application/json"},
            params={"key": "key"},
            json={"contents": [{"parts": [{"text": "hello"}]}]},
        )
    return result


def test_generate_sends_prompt_and_returns_text():
    assert asyncio.run(run_generate()) == "hi"
