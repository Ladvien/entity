import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import asyncpg

from config.environment import load_env
from pipeline.plugins.resources.postgres_database import PostgresDatabaseResource

load_env(Path(__file__).resolve().parents[1] / ".env")


async def init_resource():
    cfg = {
        "host": os.environ["DB_HOST"],
        "port": 5432,
        "name": "db",
        "username": os.environ["DB_USERNAME"],
        "password": os.environ.get("DB_PASSWORD", ""),
        "pool_min_size": 1,
        "pool_max_size": 5,
    }
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 993de08c4c8e26f1c4f76d5337df519d1e21df99
    pool = AsyncMock()
    with patch(
        "asyncpg.create_pool", new=AsyncMock(return_value=pool)
    ) as mock_create_pool:
        plugin = PostgresResource(cfg)
=======
    conn = AsyncMock()
    conn.fetchval = AsyncMock(return_value=1)
    with patch("asyncpg.connect", new=AsyncMock(return_value=conn)) as mock_connect:
        plugin = PostgresDatabaseResource(cfg)
>>>>>>> 66045f0cc3ea9a831e3ec579ceb40548cd673716
        await plugin.initialize()
        mock_create_pool.assert_awaited_with(
            database="db",
            host=os.environ["DB_HOST"],
            port=5432,
            user=os.environ["DB_USERNAME"],
            password=os.environ.get("DB_PASSWORD", ""),
            min_size=1,
            max_size=5,
        )
    return plugin, pool


def test_initialize_opens_pool():
    plugin, _ = asyncio.run(init_resource())
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 993de08c4c8e26f1c4f76d5337df519d1e21df99
    assert plugin._pool is not None


async def run_health_check():
    plugin = PostgresResource({})
    pool = AsyncMock()
<<<<<<< HEAD
=======
    assert plugin._connection is not None
    assert plugin.has_vector_store


async def run_health_check():
    plugin = PostgresDatabaseResource({})
>>>>>>> 66045f0cc3ea9a831e3ec579ceb40548cd673716
=======
>>>>>>> 993de08c4c8e26f1c4f76d5337df519d1e21df99
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


def test_malicious_table_name_is_quoted():
    async def run():
        cfg = {
            "host": os.environ["DB_HOST"],
            "port": 5432,
            "name": "db",
            "username": os.environ["DB_USERNAME"],
            "password": os.environ.get("DB_PASSWORD", ""),
            "db_schema": "public; DROP SCHEMA x;",
            "history_table": "history; DROP TABLE y;",
        }
        conn = AsyncMock()
        with patch("asyncpg.connect", new=AsyncMock(return_value=conn)):
            plugin = PostgresResource(cfg)
            await plugin.initialize()
            expected_table = (
                f'{asyncpg.utils._quote_ident(cfg["db_schema"])}.'
                f'{asyncpg.utils._quote_ident(cfg["history_table"])}'
            )
            executed_query = conn.execute.await_args.args[0]
            assert expected_table in executed_query

    asyncio.run(run())
