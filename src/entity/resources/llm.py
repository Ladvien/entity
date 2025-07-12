from __future__ import annotations

"""Canonical LLM resource."""

from typing import Any, Dict

from .base import AgentResource
from .interfaces.llm import LLMResource as LLMProvider


class LLM(AgentResource):
    """Simple LLM wrapper."""

    name = "llm"
    dependencies: list[str] = ["llm_provider?"]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.provider: LLMProvider | None = None

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None
