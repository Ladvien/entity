from __future__ import annotations

from typing import Any, Dict, List

from pipeline.plugins import ResourcePlugin
from pipeline.resources import LLM
from pipeline.stages import PipelineStage


class LLMResource(ResourcePlugin, LLM):
    """Base class for language model resources."""

    stages = [PipelineStage.PARSE]
    name = "llm"
    aliases: List[str] = ["llm"]

    async def _execute_impl(self, context) -> None:
        return None
