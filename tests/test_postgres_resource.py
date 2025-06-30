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
    conn = AsyncMock()
    with patch("asyncpg.connect", new=AsyncMock(return_value=conn)) as mock_connect:
        plugin = PostgresResource(cfg)
        await plugin.initialize()
        mock_connect.assert_awaited_with(
            database="db",
            host=os.environ["DB_HOST"],
            port=5432,
            user=os.environ["DB_USERNAME"],
            password=os.environ.get("DB_PASSWORD", ""),
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
