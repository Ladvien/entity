import asyncio
from unittest.mock import AsyncMock, patch

from pipeline.plugins.resources.claude import ClaudeResource


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - stub
        pass

    def json(self):
        return {"content": [{"text": "hi"}]}


async def run_generate():
    resource = ClaudeResource(
        {
            "api_key": "key",
            "model": "claude-3",
            "base_url": "https://api.anthropic.com",
        }
    )
    with patch(
        "httpx.AsyncClient.post", new=AsyncMock(return_value=FakeResponse())
    ) as mock_post:
        result = await resource.generate("hello")
        mock_post.assert_awaited_with(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": "key", "anthropic-version": "2023-06-01"},
            json={
                "model": "claude-3",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
    return result


def test_generate_sends_prompt_and_returns_text():
    assert asyncio.run(run_generate()) == "hi"
