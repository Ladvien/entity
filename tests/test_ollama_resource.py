import asyncio
from unittest.mock import AsyncMock, patch

from pipeline.plugins.resources.ollama_llm import OllamaLLMResource


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - simple stub
        pass

    def json(self):
        return {"response": "hi"}


async def run_generate():
    resource = OllamaLLMResource(
        {"base_url": "http://ollama:11434", "model": "tinyllama"}
    )
    with patch(
        "httpx.AsyncClient.post", new=AsyncMock(return_value=FakeResponse())
    ) as mock_post:
        result = await resource.generate("hello")
        mock_post.assert_called_with(
            "http://ollama:11434/api/generate",
            json={"model": "tinyllama", "prompt": "hello"},
        )
    return result


def test_generate_sends_prompt_and_returns_text():
    result = asyncio.run(run_generate())
    assert result == "hi"
