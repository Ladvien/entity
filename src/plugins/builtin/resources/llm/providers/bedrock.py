from __future__ import annotations

"""Adapter for AWS Bedrock runtime."""
import json
from typing import Any, AsyncIterator, Dict, List

import aioboto3

from pipeline.exceptions import ResourceError
from pipeline.state import LLMResponse
from pipeline.validation import ValidationResult

from .base import BaseProvider


class BedrockProvider(BaseProvider):
    """Adapter for AWS Bedrock runtime."""

    name = "bedrock"

    def __init__(self, config: Dict) -> None:
        super().__init__(config)
        self.model_id: str = str(config.get("model_id", ""))
        self.region: str = str(config.get("region", "us-east-1"))
        self.params = {
            k: v
            for k, v in config.items()
            if k
            not in {
                "model_id",
                "region",
                "retries",
                "base_url",
                "model",
                "api_key",
            }
        }

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        if not config.get("model_id"):
            return ValidationResult.error_result("'model_id' is required")
        return ValidationResult.success_result()

    async def _invoke(self, prompt: str) -> str:
        payload = {"prompt": prompt, **self.params}

        async def call() -> str:
            client_kwargs = {"region_name": self.region}
            endpoint_url = self.params.get("endpoint_url")
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url
            async with aioboto3.client("bedrock-runtime", **client_kwargs) as client:
                response = await client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(payload),
                    contentType="application/json",
                    accept="application/json",
                )
                body = json.loads(response["body"].read())
                return str(body.get("outputText") or body.get("completion", ""))

        try:
            return await self.http._breaker.call(call)
        except Exception as exc:  # pragma: no cover - bubble up
            raise ResourceError("bedrock provider request failed") from exc

    async def generate(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> LLMResponse:
        text = await self._invoke(prompt)
        return LLMResponse(content=text)

    async def stream(
        self, prompt: str, functions: List[Dict[str, Any]] | None = None
    ) -> AsyncIterator[str]:
        yield await (await self.generate(prompt)).content
