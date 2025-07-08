from __future__ import annotations

"""Shared HTTP logic for LLM providers."""
from typing import Any, AsyncIterator, Dict, Optional

import httpx

from pipeline.validation import ValidationResult

from .http_llm_resource import HttpLLMResource
from .llm_base import LLM


class HTTPProviderResource(LLM):
    """Reusable base class for HTTP based providers."""

    name = "http_provider"
    requires_api_key: bool = False

    def __init__(self, config: Dict) -> None:
        self.http = HttpLLMResource(config, require_api_key=self.requires_api_key)
        self.retry_attempts = int(config.get("retries", 3))
        self.timeout = float(config.get("timeout", 30))
        self._client: httpx.AsyncClient | None = None

    @classmethod
    def validate_config(cls, config: Dict) -> ValidationResult:
        """Validate configuration using :class:`HttpLLMResource`."""
        return HttpLLMResource(
            config, require_api_key=cls.requires_api_key
        ).validate_config()

    async def __aenter__(self) -> "HTTPProviderResource":
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.aclose()
        self._client = None

    async def validate_runtime(self) -> ValidationResult:
        if not self.http.base_url:
            return ValidationResult.error_result("'base_url' is required")
        return ValidationResult.success_result()

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
        async for chunk in self.http.stream_request(url, payload, headers, params):
            yield chunk
