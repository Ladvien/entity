from __future__ import annotations

<<<<<<< HEAD
<<<<<<< HEAD
from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional, Protocol

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class StorageBackend(Protocol):
    """Protocol for asynchronous storage backends.

    Storage implementations should provide basic CRUD operations and a
    generic command execution method.  All methods return awaitables to
    support async resources such as databases or object stores.
    """

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


class StorageResource(ResourcePlugin, StorageBackend):
    """Base class for storage resources with connection pooling support.

    Subclasses provide the logic to create the connection pool during
    :meth:`initialize`.  The helper :meth:`connection` context manager
    ensures connections are acquired and released properly.
    """

    stages = [PipelineStage.PARSE]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._pool: Optional[Any] = None

    async def initialize(self) -> None:
        """Create the underlying connection pool.

        Subclasses must set :attr:`_pool` to an object exposing ``acquire``
        and ``release`` coroutines.  The default implementation does
        nothing.
        """

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

    @abstractmethod
    async def _do_health_check(self, connection: Any) -> None:
        """Subclasses run a minimal query to verify ``connection`` works."""

    # --- StorageBackend API -------------------------------------------------
    @abstractmethod
    async def save(self, key: str, data: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def load(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def query(self, query: str) -> list[Any]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def execute(self, command: str, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError
=======
from typing import List, Protocol

from pipeline.context import ConversationEntry


class StorageBackend(Protocol):
    """Protocol for resources that persist conversation history."""

    async def save_history(
        self, conversation_id: str, history: List[ConversationEntry]
    ) -> None: ...

    async def load_history(self, conversation_id: str) -> List[ConversationEntry]: ...
>>>>>>> a2fde49ed50a219b934336428d39351655a5f9c5
=======
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
>>>>>>> 5e83dad2333366e3475cc1780350f7148fd6a771
