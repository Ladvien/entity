"""Shared pytest fixtures for integration tests.

This module configures Docker-based services for tests. The Postgres and
Ollama containers start once per session and shut down automatically.
"""

from pathlib import Path
import os
import sys
import asyncio
from contextlib import asynccontextmanager

import asyncpg
import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("ENTITY_AUTO_INIT", "0")

from entity.infrastructure import DuckDBInfrastructure
from entity.resources import Memory, LLM
from entity.resources.interfaces.duckdb_resource import DuckDBResource
from entity.resources.interfaces.database import DatabaseResource
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


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig: pytest.Config) -> str:
    """Return path to the docker compose file."""
    return str(Path(pytestconfig.rootpath) / "tests" / "docker-compose.yml")


def _postgres_ready(dsn: str) -> bool:
    async def _check() -> bool:
        try:
            conn = await asyncpg.connect(dsn)
            await conn.execute("SELECT 1")
            await conn.close()
            return True
        except Exception:
            return False

    return asyncio.get_event_loop().run_until_complete(_check())


@pytest.fixture(scope="session")
def postgres_dsn(docker_ip: str, docker_services) -> str:
    """Start the Postgres container and return a DSN."""
    docker_services.start("postgres")
    port = docker_services.port_for("postgres", 5432)
    dsn = f"postgresql://test:test@{docker_ip}:{port}/test_db"
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.5, check=lambda: _postgres_ready(dsn)
    )
    return dsn


class AsyncPGDatabase(DatabaseResource):
    """Database adapter using ``psycopg`` against Postgres."""

    def __init__(self, dsn: str) -> None:
        super().__init__({})
        self._dsn = dsn

    @asynccontextmanager
    async def connection(self):
        conn = psycopg.connect(self._dsn)
        try:
            yield conn
        finally:
            conn.close()

    def get_connection_pool(self):  # pragma: no cover - simplify
        return self._dsn


@pytest.fixture(scope="session")
async def pg_memory(postgres_dsn: str) -> Memory:
    """Memory resource backed by Postgres."""
    db = AsyncPGDatabase(postgres_dsn)
    mem = Memory({})
    mem.database = db
    mem.vector_store = None
    await mem.initialize()
    try:
        yield mem
    finally:
        async with db.connection() as conn:
            conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
            conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")


@pytest.fixture(scope="session")
def ollama_url(docker_ip: str, docker_services) -> str:
    """Start the Ollama container and return its base URL."""
    docker_services.start("ollama")
    port = docker_services.port_for("ollama", 11434)
    url = f"http://{docker_ip}:{port}"

    def _ready() -> bool:
        try:
            import httpx

            resp = httpx.post(f"{url}/api/generate", json={"prompt": "ping"})
            return resp.status_code == 200
        except Exception:
            return False

    docker_services.wait_until_responsive(timeout=30.0, pause=0.5, check=_ready)
    return url


@pytest.fixture(scope="session")
async def ollama_llm(ollama_url: str) -> LLM:
    """LLM resource using the Ollama container."""
    from plugins.builtin.resources.ollama_llm import OllamaLLMResource

    llm_provider = OllamaLLMResource({"base_url": ollama_url, "model": "test"})
    llm = LLM({"pool": {"min_size": 1, "max_size": 1}})
    llm.provider = llm_provider
    await llm.initialize()
    yield llm
