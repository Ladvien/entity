import asyncio
from unittest.mock import AsyncMock, patch

from pipeline.plugins.resources.llm.unified import UnifiedLLMResource


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - stub
        pass

    def json(self):
        return {"choices": [{"message": {"content": "hi"}}]}


async def run_generate():
    resource = UnifiedLLMResource(
        {
            "provider": "openai",
            "api_key": "key",
            "model": "gpt-4",
            "base_url": "https://api.openai.com",
        }
    )
    with patch(
        "httpx.AsyncClient.post", new=AsyncMock(return_value=FakeResponse())
    ) as mock_post:
        result = await resource.generate("hello")
        mock_post.assert_awaited_with(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": "Bearer key"},
            json={"model": "gpt-4", "messages": [{"role": "user", "content": "hello"}]},
            params=None,
        )
    return result


def test_generate_sends_prompt_and_returns_text():
    assert asyncio.run(run_generate()) == "hi"
