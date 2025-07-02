from __future__ import annotations

<<<<<<< HEAD
from typing import Any, Protocol


class Memory(Protocol):
    """Protocol for simple key/value memory stores."""

    def get(self, key: str, default: Any | None = None) -> Any: ...

    def set(self, key: str, value: Any) -> None: ...
=======
from abc import ABC, abstractmethod
from typing import Any


class Memory(ABC):
    """Interface for memory storage resources."""

    async def initialize(self) -> None:  # pragma: no cover - optional
        """Optional async initialization hook."""
        return None

    @abstractmethod
    def get(self, key: str, default: Any | None = None) -> Any:
        """Retrieve a value from memory."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Persist ``value`` in memory under ``key``."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all values from memory."""
>>>>>>> 66045f0cc3ea9a831e3ec579ceb40548cd673716
