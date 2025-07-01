from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from pipeline.plugins import ValidationResult


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
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url, json=payload, headers=headers, params=params
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover
            raise RuntimeError(f"HTTP request failed: {exc}") from exc
        return response.json()
