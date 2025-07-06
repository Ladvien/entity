import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

from config.environment import load_env
from plugins.builtin.resources.llm.unified import UnifiedLLMResource

load_env(Path(__file__).resolve().parents[1] / ".env")


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - simple stub
        pass

    def json(self):
        return {"response": "hi"}


async def run_generate():
    resource = UnifiedLLMResource(
        {
            "provider": "ollama",
            "base_url": os.environ["OLLAMA_BASE_URL"],
            "model": os.environ["OLLAMA_MODEL"],
        }
    )
    with patch(
        "httpx.AsyncClient.post", new=AsyncMock(return_value=FakeResponse())
    ) as mock_post:
        result = await resource.generate("hello")
        mock_post.assert_called_with(
            f"{os.environ['OLLAMA_BASE_URL']}/api/generate",
            json={"model": os.environ["OLLAMA_MODEL"], "prompt": "hello"},
            headers=None,
            params=None,
        )
    return result


def test_generate_sends_prompt_and_returns_text():
    result = asyncio.run(run_generate())
    assert result == "hi"
