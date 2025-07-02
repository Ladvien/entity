from __future__ import annotations

import warnings
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional

import asyncpg

<<<<<<< HEAD
from pipeline.context import ConversationEntry
from pipeline.base_plugins import ResourcePlugin
=======
from pipeline.plugins import ResourcePlugin
from pipeline.resources import StorageBackend
>>>>>>> 5e83dad2333366e3475cc1780350f7148fd6a771
from pipeline.stages import PipelineStage


class ConnectionPoolResource(ResourcePlugin):
    """Generic async connection pool resource."""

    stages = [PipelineStage.PARSE]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._pool: Optional[Any] = None

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[Any]:
        conn = await self.acquire()
        try:
            yield conn
        finally:
            await self.release(conn)

    async def acquire(self) -> Any:
        if self._pool is None:
            raise RuntimeError("Pool not initialized")
        return await self._pool.acquire()

    async def release(self, connection: Any) -> None:
        if self._pool is not None:
            await self._pool.release(connection)

    async def shutdown(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    async def health_check(self) -> bool:
        if self._pool is None:
            return False
        async with self.connection() as conn:
            try:
                await self._do_health_check(conn)
                return True
            except Exception:
                return False

    async def _do_health_check(self, connection: Any) -> None:
        raise NotImplementedError


class PostgresStorageBackend(ConnectionPoolResource, StorageBackend):
    """Asynchronous PostgreSQL storage backend."""

    name = "database"

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._min_size = int(self.config.get("pool_min_size", 1))
        self._max_size = int(self.config.get("pool_max_size", 5))

    async def initialize(self) -> None:
        self.logger.info(
            "Creating Postgres connection pool", extra={"config": self.config}
        )
        self._pool = await asyncpg.create_pool(
            database=str(self.config.get("name")),
            host=str(self.config.get("host", "localhost")),
            port=int(self.config.get("port", 5432)),
            user=str(self.config.get("username")),
            password=str(self.config.get("password")),
            min_size=self._min_size,
            max_size=self._max_size,
        )

    async def _execute_impl(self, context) -> Any:  # pragma: no cover - no op
        return None

    async def _do_health_check(self, connection: asyncpg.Connection) -> None:
        await connection.fetchval("SELECT 1")

    async def execute(self, query: str, *args: Any) -> Any:
        if self._pool is None:
            raise RuntimeError("Pool not initialized")
        async with self.connection() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> List[Any]:
        if self._pool is None:
            raise RuntimeError("Pool not initialized")
        async with self.connection() as conn:
            return await conn.fetch(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        if self._pool is None:
            raise RuntimeError("Pool not initialized")
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)


class PostgresPoolResource(PostgresStorageBackend):
    """Deprecated compatibility wrapper."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        warnings.warn(
            "PostgresPoolResource is deprecated, use PostgresStorageBackend instead",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


# Backwards compatibility alias
PostgresResource = PostgresPoolResource
