from __future__ import annotations

from typing import Any, Iterable, Protocol


class StorageBackend(Protocol):
    """Interface for basic async storage backends."""

    async def execute(self, query: str, *args: Any) -> Any:
        """Run ``query`` without returning rows."""
        ...

    async def fetch(self, query: str, *args: Any) -> Iterable[Any]:
        """Return rows for ``query``."""
        ...

    async def fetchval(self, query: str, *args: Any) -> Any:
        """Return a single value for ``query``."""
        ...
