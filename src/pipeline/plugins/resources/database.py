from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, Optional

from pipeline.plugins import ResourcePlugin
from pipeline.stages import PipelineStage


class DatabaseResource(ResourcePlugin):
    """Generic asynchronous database resource using a connection pool."""

    stages = [PipelineStage.PARSE]

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config)
        self._pool: Optional[Any] = None

    async def initialize(self) -> None:
        self._pool = await self._create_pool()

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

    async def _create_pool(self) -> Any:
        """Create and return a connection pool."""
        raise NotImplementedError

    async def _do_health_check(self, connection: Any) -> None:
        """Run a health check query using ``connection``."""
        raise NotImplementedError
