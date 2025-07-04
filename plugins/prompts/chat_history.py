from __future__ import annotations

from pipeline.plugins.prompts.memory import MemoryPlugin


class ChatHistory(MemoryPlugin):
    """Alias for ``MemoryPlugin`` for backward compatibility."""

    pass


__all__ = ["ChatHistory"]
