import asyncio
from unittest.mock import AsyncMock, patch

from pipeline import (
    MetricsCollector,
    PipelineState,
    SimpleContext,
    SystemInitializer,
    SystemRegistries,
)
from pipeline.plugins.resources.llm.unified import UnifiedLLMResource


class FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - stub
        pass

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": "hi"}]}}]}


async def run_generate():
    resource = UnifiedLLMResource(
        {
            "provider": "gemini",
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


def test_context_get_llm_with_provider():
    cfg = {
        "plugins": {
            "resources": {
                "llm": {
                    "type": "pipeline.plugins.resources.llm.unified:UnifiedLLMResource",
                    "provider": "gemini",
                    "api_key": "key",
                    "model": "gemini-pro",
                    "base_url": "https://generativelanguage.googleapis.com",
                }
            }
        }
    }
    initializer = SystemInitializer.from_dict(cfg)
    plugin_reg, resource_reg, tool_reg = asyncio.run(initializer.initialize())
    state = PipelineState(conversation=[], pipeline_id="1", metrics=MetricsCollector())
    ctx = SimpleContext(state, SystemRegistries(resource_reg, tool_reg, plugin_reg))
    assert isinstance(ctx.get_llm(), UnifiedLLMResource)
