import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

from config.environment import load_env
from pipeline.plugins.resources.postgres import PostgresResource

load_env(Path(__file__).resolve().parents[1] / ".env")


async def init_resource():
    cfg = {
        "host": os.environ["DB_HOST"],
        "port": 5432,
        "name": "db",
        "username": os.environ["DB_USERNAME"],
        "password": os.environ.get("DB_PASSWORD", ""),
    }
    pool = AsyncMock()
    with patch(
        "asyncpg.create_pool", new=AsyncMock(return_value=pool)
    ) as mock_create_pool:
        plugin = PostgresResource(cfg)
        await plugin.initialize()
        mock_create_pool.assert_awaited_with(
            database="db",
            host=os.environ["DB_HOST"],
            port=5432,
            user=os.environ["DB_USERNAME"],
            password=os.environ.get("DB_PASSWORD", ""),
        )
    return plugin, pool


def test_initialize_opens_pool():
    plugin, _ = asyncio.run(init_resource())
    assert plugin._pool is not None


async def run_health_check():
    plugin = PostgresResource({})
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetchval = AsyncMock(return_value=1)
    pool.acquire = AsyncMock(return_value=conn)
    pool.release = AsyncMock()
    plugin._pool = pool
    result = await plugin.health_check()
    conn.fetchval.assert_awaited_with("SELECT 1")
    pool.release.assert_awaited_with(conn)
    return result


def test_health_check_runs_query():
    assert asyncio.run(run_health_check())
