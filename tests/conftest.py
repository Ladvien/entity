from pathlib import Path
import os
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("ENTITY_AUTO_INIT", "0")

from entity.infrastructure import DuckDBInfrastructure
from entity.resources import Memory
from entity.resources.interfaces.duckdb_resource import DuckDBResource
from entity.core.resources.container import ResourceContainer


@pytest.fixture()
async def memory_db(tmp_path: Path) -> Memory:
    db_path = tmp_path / "memory.duckdb"
    db_backend = DuckDBInfrastructure({"path": str(db_path)})
    await db_backend.initialize()
    async with db_backend.connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS conversation_history (conversation_id TEXT, role TEXT, content TEXT, metadata TEXT, timestamp TEXT)"
        )
    db = DuckDBResource({})
    db.database = db_backend
    mem = Memory(config={})
    mem.database = db
    mem.vector_store = None
    await mem.initialize()
    try:
        yield mem
    finally:
        await db_backend.shutdown()


@pytest.fixture()
def resource_container() -> ResourceContainer:
    container = ResourceContainer()
    container.register("database_backend", DuckDBInfrastructure, {}, layer=1)
    return container


@pytest.fixture(autouse=True)
def _clear_metrics_deps():
    from entity.resources.metrics import MetricsCollectorResource

    original = MetricsCollectorResource.dependencies.copy()
    original_infra = MetricsCollectorResource.infrastructure_dependencies.copy()
    MetricsCollectorResource.dependencies = []
    MetricsCollectorResource.infrastructure_dependencies = []
    try:
        yield
    finally:
        MetricsCollectorResource.dependencies = original
        MetricsCollectorResource.infrastructure_dependencies = original_infra
