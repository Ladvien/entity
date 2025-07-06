from __future__ import annotations

"""Legacy alias plugin exposing conversation history."""


from pipeline.stages import PipelineStage

from .memory import MemoryPlugin


class ChatHistory(MemoryPlugin):
    """Alias for ``MemoryPlugin`` for backward compatibility."""

    stages = [PipelineStage.PARSE, PipelineStage.DELIVER]


__all__ = ["ChatHistory"]
