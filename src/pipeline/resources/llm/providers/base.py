from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from pipeline.resources.http_llm_resource import HttpLLMResource
from pipeline.resources.llm_base import LLM
from pipeline.validation import ValidationResult


class BaseProvider(LLM):
    """Base class for HTTP LLM providers."""

    name = "base"
    requires_api_key: bool = False

    def __init__(self, config: Dict) -> None:
        self.http = HttpLLMResource(config, require_api_key=self.requires_api_key)
        self.retry_attempts = int(config.get("retries", 3))

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        return HttpLLMResource(
            config, require_api_key=cls.requires_api_key
        ).validate_config()

    async def _post_with_retry(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        last_exc: Exception | None = None
        for attempt in range(self.retry_attempts):
            try:
                return await self.http._post_request(url, payload, headers, params)
            except Exception as exc:  # noqa: BLE001 - retry
                last_exc = exc
                await asyncio.sleep(2**attempt)
        raise RuntimeError(f"{self.name} provider request failed") from last_exc
