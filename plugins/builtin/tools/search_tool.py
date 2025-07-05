from __future__ import annotations

"""Web search tool leveraging DuckDuckGo's API."""

from typing import Any, Dict

import httpx
from pydantic import BaseModel

from pipeline.base_plugins import ToolPlugin
from pipeline.stages import PipelineStage
from pipeline.validation.input import validate_params


class SearchTool(ToolPlugin):
    """Simple search tool using DuckDuckGo's public API.

    Embodies **Immediate Tool Access (24)** so prompts can query the web at any
    stage.
    """

    stages = [PipelineStage.DO]
    required_params = ["query"]

    class Params(BaseModel):
        query: str

    @validate_params(Params)
    async def execute_function(self, params: Params) -> str:
        query = params.query

        url = "https://api.duckduckgo.com/"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    url,
                    params={
                        "q": query,
                        "format": "json",
                        "no_redirect": 1,
                        "no_html": 1,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network error path
            raise RuntimeError(f"Search request failed: {exc}") from exc

        data = response.json()
        topics = data.get("RelatedTopics")
        if topics and isinstance(topics, list):
            first = topics[0]
            if isinstance(first, dict) and first.get("Text"):
                return str(first["Text"])
        return "No results found."

    async def execute(self, params: Dict[str, Any]) -> Any:  # type: ignore[override]
        return await self.execute_function(params)


__all__ = ["SearchTool"]
