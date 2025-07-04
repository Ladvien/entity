from __future__ import annotations

import asyncio
import io
from unittest.mock import patch

from plugins.resources.llm.unified import UnifiedLLMResource


class FakeClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def invoke_model(self, **kwargs):
        self.kwargs = kwargs
        return {"body": io.BytesIO(b'{"outputText":"hi"}')}


async def run_generate():
    resource = UnifiedLLMResource({"provider": "bedrock", "model_id": "mi"})
    with patch("aioboto3.client", return_value=FakeClient()) as mock_client:
        result = await resource.generate("hello")
        mock_client.assert_called_with("bedrock-runtime", region_name="us-east-1")
        assert mock_client.return_value.kwargs["modelId"] == "mi"
    return result


def test_generate_sends_prompt_and_returns_text():
    assert asyncio.run(run_generate()) == "hi"
