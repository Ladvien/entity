import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import asyncpg
from pgvector import Vector

from config.environment import load_env
from pipeline.plugins.resources.vector_memory import VectorMemoryResource

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
    pool.execute = AsyncMock()
    pool.fetch = AsyncMock()
    with (
        patch(
            "asyncpg.create_pool", new=AsyncMock(return_value=pool)
        ) as mock_create_pool,
        patch(
            "pipeline.plugins.resources.vector_memory.register_vector",
            new=AsyncMock(),
        ) as mock_register,
    ):
        plugin = VectorMemoryResource(cfg)
        await plugin.initialize()
        mock_create_pool.assert_awaited_with(
            database="db",
            host=os.environ["DB_HOST"],
            port=5432,
            user=os.environ["DB_USERNAME"],
            password=os.environ.get("DB_PASSWORD", ""),
        )
        mock_register.assert_awaited_with(pool)
    return plugin, pool


def test_add_embedding_inserts_row():
    async def run():
        plugin, pool = await init_resource()
        with patch.object(plugin, "_embed", return_value=[1.0, 2.0, 3.0]):
            await plugin.add_embedding("hello")
<<<<<<< HEAD
            conn.execute.assert_awaited_with(
                f"INSERT INTO {asyncpg.utils._quote_ident('vector_memory')} (text, embedding) VALUES ($1, $2)",
=======
            pool.execute.assert_awaited_with(
                "INSERT INTO vector_memory (text, embedding) VALUES ($1, $2)",
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc
                "hello",
                Vector([1.0, 2.0, 3.0]),
            )

    asyncio.run(run())


def test_query_similar_returns_texts():
    async def run():
        plugin, pool = await init_resource()
        pool.fetch = AsyncMock(return_value=[{"text": "a"}, {"text": "b"}])
        with patch.object(plugin, "_embed", return_value=[1.0, 2.0, 3.0]):
            result = await plugin.query_similar("hello", 2)
<<<<<<< HEAD
            conn.fetch.assert_awaited_with(
                f"SELECT text FROM {asyncpg.utils._quote_ident('vector_memory')} ORDER BY embedding <-> $1 LIMIT $2",
=======
            pool.fetch.assert_awaited_with(
                "SELECT text FROM vector_memory ORDER BY embedding <-> $1 LIMIT $2",
>>>>>>> 66ac501313b5b7eaa42b03d18024eecb130295bc
                Vector([1.0, 2.0, 3.0]),
                2,
            )
        return result

    assert asyncio.run(run()) == ["a", "b"]


def test_malicious_table_name_is_quoted():
    async def run():
        cfg = {
            "host": os.environ["DB_HOST"],
            "port": 5432,
            "name": "db",
            "username": os.environ["DB_USERNAME"],
            "password": os.environ.get("DB_PASSWORD", ""),
            "table": "memory; DROP TABLE z;",
        }
        conn = AsyncMock()
        with (
            patch("asyncpg.connect", new=AsyncMock(return_value=conn)),
            patch(
                "pipeline.plugins.resources.vector_memory.register_vector",
                new=AsyncMock(),
            ),
        ):
            plugin = VectorMemoryResource(cfg)
            await plugin.initialize()
            table = asyncpg.utils._quote_ident(cfg["table"])
            executed_query = conn.execute.await_args.args[0]
            assert table in executed_query
            with patch.object(plugin, "_embed", return_value=[1.0, 2.0, 3.0]):
                await plugin.add_embedding("x")
                conn.execute.assert_awaited_with(
                    f"INSERT INTO {table} (text, embedding) VALUES ($1, $2)",
                    "x",
                    Vector([1.0, 2.0, 3.0]),
                )

    asyncio.run(run())
