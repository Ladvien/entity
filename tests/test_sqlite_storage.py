import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

from pipeline.plugins.resources.sqlite_storage import SQLiteStorage


async def init_resource():
    cfg = {"path": "./db.sqlite"}
    conn = AsyncMock()
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    with patch("aiosqlite.connect", new=AsyncMock(return_value=conn)) as mock_connect:
        plugin = SQLiteStorage(cfg)
        await plugin.initialize()
        mock_connect.assert_awaited()
    return plugin, conn


def test_initialize_opens_pool():
    plugin, _ = asyncio.run(init_resource())
    assert plugin._size >= 1


def test_health_check_runs_query():
    async def run():
        plugin = SQLiteStorage({})
        plugin.fetch = AsyncMock(return_value=[(1,)])
        result = await plugin.health_check()
        plugin.fetch.assert_awaited_with("SELECT 1")
        return result

    assert asyncio.run(run())
