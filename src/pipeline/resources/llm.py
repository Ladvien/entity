"""Unified LLM resource stub used in tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import httpx


@dataclass
class _Provider:
    name: str
    config: Dict[str, Any]

    async def generate(self, prompt: str) -> str:
        if self.name == "gemini":
            url = f"{self.config['base_url'].rstrip('/')}/v1beta/models/{self.config['model']}:generateContent?key={self.config['api_key']}"
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=data)
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        if self.name == "claude":
            url = f"{self.config['base_url'].rstrip('/')}/v1/messages"
            data = {
                "model": self.config["model"],
                "messages": [{"role": "user", "content": prompt}],
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=data)
            return resp.json()["content"][0]["text"]
        # Echo and other providers simply return the prompt
        return prompt


class UnifiedLLMResource:
    """Simplified multi-provider LLM wrapper."""

    dependencies: list[str] = []

    def __init__(self, config: Dict[str, Any]) -> None:
        self._providers = [_Provider(config.get("provider", ""), config)]

    async def generate(self, prompt: str) -> str:
        return await self._providers[0].generate(prompt)
