from __future__ import annotations

"""Legacy alias plugin exposing conversation history."""


from .memory import MemoryPlugin


class ChatHistory(MemoryPlugin):
    """Alias for ``MemoryPlugin`` for backward compatibility."""

    pass


__all__ = ["ChatHistory"]
