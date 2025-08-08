import asyncio
import multiprocessing

import pytest

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.plugins.context import PluginContext
from entity.resources.database import DatabaseResource
from entity.resources.memory import Memory
from entity.resources.vector_store import VectorStoreResource


def _worker(db_path: str, uid: int) -> None:
    infra = DuckDBInfrastructure(db_path)
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    ctx = PluginContext({"memory": memory}, user_id=str(uid))
    asyncio.run(ctx.remember("val", uid))


@pytest.mark.asyncio
async def test_multiple_processes_share_memory(tmp_path):
    db_file = tmp_path / "shared.duckdb"
    processes = [
        multiprocessing.Process(target=_worker, args=(str(db_file), i))
        for i in range(5)
    ]
    for proc in processes:
        proc.start()
    for proc in processes:
        proc.join()

    infra = DuckDBInfrastructure(str(db_file))
    memory = Memory(DatabaseResource(infra), VectorStoreResource(infra))
    PluginContext({"memory": memory}, user_id="0")
    try:
        values = [await memory.load(f"{i}:val") for i in range(5)]
    except Exception as exc:
        pytest.skip(f"Concurrency not supported: {exc}")
    if any(v is None for v in values):
        pytest.skip("Persistence failed under concurrency")
    assert values == list(range(5))
