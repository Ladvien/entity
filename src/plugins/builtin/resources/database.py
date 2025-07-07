from __future__ import annotations

"""Database-backed conversation storage."""
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncIterator, List, Optional, Protocol

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from pipeline.state import ConversationEntry

from pipeline.validation import ValidationResult
from plugins.builtin.resources.base import BaseResource


class StorageBackend(Protocol):
    """Protocol for asynchronous database backends."""

    async def save(self, key: str, data: Any) -> None:
        """Persist ``data`` under ``key``."""

    async def load(self, key: str) -> Any:
        """Retrieve the value previously stored for ``key``."""

    async def query(self, query: str) -> list[Any]:
        """Run ``query`` against the backend and return results."""

    async def delete(self, key: str) -> None:
        """Remove ``key`` and its associated value."""

    async def execute(self, command: str, *args: Any, **kwargs: Any) -> Any:
        """Execute an arbitrary ``command`` on the backend."""

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        """Persist conversation ``history`` for ``conversation_id``."""

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        """Retrieve stored history for ``conversation_id``."""


class DatabaseResource(BaseResource, StorageBackend, ABC):
    """Unified base class for database resources."""

    name = "database"

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config)
        self.has_vector_store = False
        self._pool: Optional[Any] = None

    async def initialize(self) -> None:  # pragma: no cover - optional
        """Create the underlying connection pool if needed."""

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        """Yield a pooled connection."""

        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

    async def acquire(self) -> Any:
        """Acquire a connection from the pool."""

        if self._pool is None:
            raise RuntimeError("Pool not initialized")
        return await self._pool.acquire()  # type: ignore[no-any-return]

    async def release(self, connection: Any) -> None:
        """Return ``connection`` to the pool."""

        if self._pool is not None:
            await self._pool.release(connection)

    async def shutdown(self) -> None:
        """Close the connection pool if it exists."""

        if self._pool is not None:
            await self._pool.close()

    async def health_check(self) -> bool:
        """Return ``True`` if a simple command succeeds."""

        if self._pool is None:
            return False
        async with self.connection() as conn:
            try:
                await self._do_health_check(conn)
                return True
            except Exception:
                return False

    async def validate_runtime(self) -> ValidationResult:
        """Validate runtime by checking database connectivity."""

        return (
            ValidationResult.success_result()
            if await self.health_check()
            else ValidationResult.error_result("database connectivity failed")
        )

    @abstractmethod
    async def _do_health_check(self, connection: Any) -> None:
        """Subclasses run a minimal query to verify ``connection`` works."""

    # --- StorageBackend API -------------------------------------------------
    async def save(self, key: str, data: Any) -> None:
        raise NotImplementedError

    async def load(self, key: str) -> Any:
        raise NotImplementedError

    async def query(self, query: str) -> list[Any]:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError

    async def execute(self, command: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    # Conversation history helpers -----------------------------------------
    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None:
        """Persist conversation ``history``."""
        raise NotImplementedError

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]:
        """Retrieve stored history for ``conversation_id``."""
        raise NotImplementedError
