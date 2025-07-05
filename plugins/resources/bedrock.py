from __future__ import annotations

"""Adapter for AWS Bedrock runtime."""
import json
from typing import Dict

import aioboto3

from pipeline.validation import ValidationResult
from plugins.resources.llm_resource import LLMResource


class BedrockResource(LLMResource):
    """LLM resource for AWS Bedrock."""

    name = "bedrock"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self.region = str(self.config.get("region", "us-east-1"))
        self.model_id = str(self.config.get("model_id", ""))
        self.params = self.extract_params(self.config, ["region", "model_id"])

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        if not config.get("model_id"):
            return ValidationResult.error_result("'model_id' is required")
        return ValidationResult.success_result()

    async def generate(self, prompt: str) -> str:
        if not self.validate_config(self.config).valid:
            raise RuntimeError("Bedrock resource not properly configured")
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

    __call__ = generate
