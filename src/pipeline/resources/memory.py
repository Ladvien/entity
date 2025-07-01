from __future__ import annotations

from typing import Any, Protocol


class Memory(Protocol):
    """Protocol for simple key/value memory stores."""

    def get(self, key: str, default: Any | None = None) -> Any: ...

    def set(self, key: str, value: Any) -> None: ...
