from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Dict

from entity.core.plugins import ResourcePlugin


class _DummyConn:
    async def execute(self, *args: Any, **kwargs: Any) -> None:
        return None


class _DummyPool:
    async def acquire(self) -> _DummyConn:
        return _DummyConn()

    async def release(self, _conn: _DummyConn) -> None:
        return None

    async def close(self) -> None:  # pragma: no cover - placeholder
        return None


class PostgresResource(ResourcePlugin):
    """Minimal Postgres resource stub used in tests."""

    name = "postgres"
    stages: list = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self._pool = _DummyPool()

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def initialize(self) -> None:
        return None

    @asynccontextmanager
    async def connection(self) -> Any:
        conn = await self._pool.acquire()
        try:
            yield conn
        finally:
            await self._pool.release(conn)
