import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

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
    conn = AsyncMock()
    with (
        patch("asyncpg.connect", new=AsyncMock(return_value=conn)) as mock_connect,
        patch(
            "pipeline.plugins.resources.vector_memory.register_vector",
            new=AsyncMock(),
        ) as mock_register,
    ):
        plugin = VectorMemoryResource(cfg)
        await plugin.initialize()
        mock_connect.assert_awaited_with(
            database="db",
            host=os.environ["DB_HOST"],
            port=5432,
            user=os.environ["DB_USERNAME"],
            password=os.environ.get("DB_PASSWORD", ""),
        )
        mock_register.assert_awaited_with(conn)
    return plugin, conn


def test_add_embedding_inserts_row():
    async def run():
        plugin, conn = await init_resource()
        with patch.object(plugin, "_embed", return_value=[1.0, 2.0, 3.0]):
            await plugin.add_embedding("hello")
            conn.execute.assert_awaited_with(
                "INSERT INTO vector_memory (text, embedding) VALUES ($1, $2)",
                "hello",
                Vector([1.0, 2.0, 3.0]),
            )

    asyncio.run(run())


def test_query_similar_returns_texts():
    async def run():
        plugin, conn = await init_resource()
        conn.fetch = AsyncMock(return_value=[{"text": "a"}, {"text": "b"}])
        with patch.object(plugin, "_embed", return_value=[1.0, 2.0, 3.0]):
            result = await plugin.query_similar("hello", 2)
            conn.fetch.assert_awaited_with(
                "SELECT text FROM vector_memory ORDER BY embedding <-> $1 LIMIT $2",
                Vector([1.0, 2.0, 3.0]),
                2,
            )
        return result

    assert asyncio.run(run()) == ["a", "b"]
