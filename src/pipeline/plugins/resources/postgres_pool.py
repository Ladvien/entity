from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Optional

import asyncpg


class PostgresConnectionPool:
    """Simple asyncpg connection pool wrapper."""

    def __init__(self, config: Dict) -> None:
        self.config = config
        self._pool: Optional[asyncpg.Pool] = None
<<<<<<< HEAD
        self._min_size = int(self.config.get("pool_min_size", 1))
        self._max_size = int(self.config.get("pool_max_size", 5))
=======
>>>>>>> 993de08c4c8e26f1c4f76d5337df519d1e21df99

    async def initialize(self) -> None:
        """Create the underlying connection pool."""
        self._pool = await asyncpg.create_pool(
            database=str(self.config.get("name")),
            host=str(self.config.get("host", "localhost")),
            port=int(self.config.get("port", 5432)),
            user=str(self.config.get("username")),
            password=str(self.config.get("password")),
<<<<<<< HEAD
            min_size=self._min_size,
            max_size=self._max_size,
=======
>>>>>>> 993de08c4c8e26f1c4f76d5337df519d1e21df99
        )

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[asyncpg.Connection]:
        """Acquire a connection from the pool."""
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)

    async def health_check(self) -> bool:
        """Return ``True`` if the pool can run a simple query."""
        if self._pool is None:
            return False
        try:
            async with self.connection() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False
