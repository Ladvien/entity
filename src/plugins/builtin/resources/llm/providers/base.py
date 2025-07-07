from __future__ import annotations

"""Base class for HTTP LLM providers."""
import asyncio
import json
from typing import Any, AsyncIterator, Dict, Optional

from pipeline.exceptions import ResourceError
from pipeline.validation import ValidationResult
from plugins.builtin.resources.http_llm_resource import HttpLLMResource
from plugins.builtin.resources.llm_base import LLM


class BaseProvider(LLM):
    """Base class for HTTP LLM providers."""

    name = "base"
    requires_api_key: bool = False

    def __init__(self, config: Dict) -> None:
        self.http = HttpLLMResource(config, require_api_key=self.requires_api_key)
        self.retry_attempts = int(config.get("retries", 3))
        self.timeout = float(config.get("timeout", 30))

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
        return await self.http._post_request(url, payload, headers, params)

    async def _stream_post_request(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        last_exc: Exception | None = None
        for attempt in range(self.retry_attempts):
            try:
                async with self.http._client.stream(
                    "POST", url, json=payload, headers=headers, params=params
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            line = line[6:]
                        if line == "[DONE]":
                            break
                        yield json.loads(line)
                return
            except Exception as exc:  # noqa: BLE001 - retry
                last_exc = exc
                await asyncio.sleep(2**attempt)
        raise ResourceError(f"{self.name} provider request failed") from last_exc
