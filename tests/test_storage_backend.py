import asyncio
from unittest.mock import AsyncMock

from pipeline.resources.database import DatabaseResource


class ExampleStorage(DatabaseResource):
    async def initialize(self) -> None:  # pragma: no cover - not used in test
        pass

    async def _do_health_check(self, connection):
        await connection.ping()

    async def save(self, key: str, data):
        async with self.connection() as conn:
            await conn.save(key, data)

    async def load(self, key: str):
        async with self.connection() as conn:
            return await conn.load(key)

    async def query(self, query: str):
        async with self.connection() as conn:
            return await conn.query(query)

    async def delete(self, key: str):
        async with self.connection() as conn:
            await conn.delete(key)

    async def execute(self, command: str, *args, **kwargs):
        async with self.connection() as conn:
            return await conn.execute(command, *args, **kwargs)


async def run_calls():
    storage = ExampleStorage({})
    conn = AsyncMock()
    conn.save = AsyncMock()
    conn.load = AsyncMock(return_value="value")
    conn.query = AsyncMock(return_value=[1])
    conn.delete = AsyncMock()
    conn.execute = AsyncMock(return_value="ok")
    conn.ping = AsyncMock()

    pool = AsyncMock()
    pool.acquire = AsyncMock(return_value=conn)
    pool.release = AsyncMock()
    storage._pool = pool

    await storage.save("k", 1)
    await storage.load("k")
    await storage.query("q")
    await storage.delete("k")
    await storage.execute("cmd")
    health = await storage.health_check()

    return {
        "conn": conn,
        "pool": pool,
        "health": health,
    }


def test_storage_resource_uses_pool():
    result = asyncio.run(run_calls())
    conn = result["conn"]
    pool = result["pool"]
    assert result["health"]
    conn.save.assert_awaited_with("k", 1)
    conn.load.assert_awaited_with("k")
    conn.query.assert_awaited_with("q")
    conn.delete.assert_awaited_with("k")
    conn.execute.assert_awaited_with("cmd")
    conn.ping.assert_awaited()
    pool.release.assert_awaited()
