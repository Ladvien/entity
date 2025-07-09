from __future__ import annotations

"""HTTP helper for LLM resources."""
import asyncio
import json
from typing import Any, AsyncIterator, Dict, Optional

import httpx

from entity.core.plugins import ValidationResult
from pipeline.cache import CacheBackend, InMemoryCache
from pipeline.exceptions import ResourceError
from pipeline.reliability import CircuitBreaker, RetryPolicy


class HttpLLMResource:
    """Helper for LLM resources using HTTP backends."""

    def __init__(self, config: Dict, require_api_key: bool = False) -> None:
        self.config = config
        self.require_api_key = require_api_key
        self.base_url: Optional[str] = config.get("base_url")
        self.model: Optional[str] = config.get("model")
        self.api_key: Optional[str] = config.get("api_key")
        self.params: Dict[str, Any] = {
            k: v for k, v in config.items() if k not in {"base_url", "model", "api_key"}
        }
        attempts = int(config.get("retries", 3))
        backoff = float(config.get("backoff", 1.0))
        self._breaker = CircuitBreaker(
            retry_policy=RetryPolicy(attempts=attempts, backoff=backoff)
        )
        self._client = httpx.AsyncClient(timeout=30)
        ttl = int(config.get("cache_ttl", 0))
        self._cache: CacheBackend | None = InMemoryCache(ttl) if ttl else None

    def validate_config(self) -> ValidationResult:
        if not self.base_url:
            return ValidationResult.error_result("'base_url' is required")
        if not self.model:
            return ValidationResult.error_result("'model' is required")
        if self.require_api_key and not self.api_key:
            return ValidationResult.error_result("'api_key' is required")
        return ValidationResult.success_result()

    async def _post_request(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        async def send() -> Dict[str, Any]:
            response = await self._client.post(
                url, json=payload, headers=headers, params=params
            )
            response.raise_for_status()
            return response.json()

        key = None
        if self._cache is not None:
            import hashlib
            import json as _json

            key = hashlib.sha256(
                _json.dumps([url, payload, headers, params], sort_keys=True).encode()
            ).hexdigest()
            cached = await self._cache.get(key)
            if cached is not None:
                return cached

        try:
            result = await self._breaker.call(send)
            if self._cache is not None and key is not None:
                await self._cache.set(key, result)
            return result
        except Exception as exc:  # pragma: no cover
            raise ResourceError(f"HTTP request failed: {exc}") from exc

    async def stream_request(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream JSONL responses with retry and backoff."""
        attempts = self._breaker.retry_policy.attempts
        last_exc: Exception | None = None
        for attempt in range(attempts):
            try:
                async with self._client.stream(
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
        raise ResourceError("HTTP request failed") from last_exc

    async def close(self) -> None:
        await self._client.aclose()
