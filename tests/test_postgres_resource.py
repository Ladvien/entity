import asyncio
from unittest.mock import AsyncMock, patch

from pipeline.plugins.resources.postgres import PostgresResource


async def init_resource():
    cfg = {
        "host": "localhost",
        "port": 5432,
        "name": "db",
        "username": "user",
        "password": "pass",
    }
    conn = AsyncMock()
    with patch("asyncpg.connect", new=AsyncMock(return_value=conn)) as mock_connect:
        plugin = PostgresResource(cfg)
        await plugin.initialize()
        mock_connect.assert_awaited_with(
            database="db",
            host="localhost",
            port=5432,
            user="user",
            password="pass",
        )
    return plugin, conn


def test_initialize_opens_connection():
    plugin, _ = asyncio.run(init_resource())
    assert plugin._connection is not None


async def run_health_check():
    plugin = PostgresResource({})
    conn = AsyncMock()
    conn.fetchval = AsyncMock(return_value=1)
    plugin._connection = conn
    result = await plugin.health_check()
    conn.fetchval.assert_awaited_with("SELECT 1")
    return result


def test_health_check_runs_query():
    assert asyncio.run(run_health_check())
