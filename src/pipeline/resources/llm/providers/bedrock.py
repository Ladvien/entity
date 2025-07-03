from __future__ import annotations

import asyncio
import json
from typing import Dict

import aioboto3

from pipeline.resources.llm_base import LLM
from pipeline.validation import ValidationResult


class BedrockProvider(LLM):
    """Adapter for AWS Bedrock runtime."""

    name = "bedrock"

    def __init__(self, config: Dict) -> None:
        self.config = config
        self.model_id: str = str(config.get("model_id", ""))
        self.region: str = str(config.get("region", "us-east-1"))
        self.params = {
            k: v
            for k, v in config.items()
            if k not in {"model_id", "region", "retries"}
        }
        self.retry_attempts = int(config.get("retries", 3))

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        if not config.get("model_id"):
            return ValidationResult.error_result("'model_id' is required")
        return ValidationResult.success_result()

    async def _invoke(self, prompt: str) -> str:
        payload = {"prompt": prompt, **self.params}
        async with aioboto3.client(
            "bedrock-runtime", region_name=self.region
        ) as client:
            response = await client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(payload),
                contentType="application/json",
                accept="application/json",
            )
            body = json.loads(response["body"].read())
            return str(body.get("outputText") or body.get("completion", ""))

    async def generate(self, prompt: str) -> str:
        last_exc: Exception | None = None
        for attempt in range(self.retry_attempts):
            try:
                return await self._invoke(prompt)
            except Exception as exc:  # noqa: BLE001 - simple retry
                last_exc = exc
                await asyncio.sleep(2**attempt)
        raise RuntimeError("bedrock provider request failed") from last_exc
