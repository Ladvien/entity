"""Shared pytest fixtures for integration tests using Docker."""

import os
import sys
import asyncio
import socket
from pathlib import Path
from contextlib import asynccontextmanager

import time
from urllib.parse import urlparse
import asyncpg
import psycopg
import pytest
from dotenv import load_dotenv

# Load environment variables from .env at project root
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# -- Pytest-docker sanity check
REQUIRE_PYTEST_DOCKER = (
    "pytest-docker is required. Run 'poetry install --with dev' to install it."
)

try:
    import pytest_docker as _  # noqa
except Exception:
    pytest.skip(REQUIRE_PYTEST_DOCKER, allow_module_level=True)


# -- Setup import path for src/
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("ENTITY_AUTO_INIT", "0")

# -- Local constants from .env
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q6_K")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", f"http://localhost:{OLLAMA_PORT}")


# -- Core imports (must follow sys.path change)
from entity.infrastructure import DuckDBInfrastructure
from entity.resources import Memory, LLM
from entity.resources.interfaces.duckdb_resource import DuckDBResource
from entity.resources.interfaces.database import DatabaseResource
from entity.core.resources.container import ResourceContainer


def _require_docker():
    pytest.importorskip("pytest_docker", reason=REQUIRE_PYTEST_DOCKER)


def _socket_open(host: str, port: int) -> bool:
    """Check if a TCP port is open."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


async def _can_connect(dsn: str) -> bool:
    try:
        conn = await asyncpg.connect(dsn)
        await conn.close()
        return True
    except Exception:
        return False


def wait_for_port(host: str, port: int, timeout: float = 30.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"Timeout waiting for {host}:{port}")


@pytest.fixture(autouse=True)
async def _clear_pg_memory(pg_memory: Memory):
    async with pg_memory.database.connection() as conn:
        await conn.execute(f"DELETE FROM {pg_memory._kv_table}")
        await conn.execute(f"DELETE FROM {pg_memory._history_table}")


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig: pytest.Config) -> str:
    _require_docker()
    return str(Path(pytestconfig.rootpath) / "tests" / "docker-compose.yml")


@pytest.fixture(scope="session")
def postgres_dsn(docker_ip: str, docker_services) -> str:
    _require_docker()
    port = docker_services.port_for("postgres", 5432)
    user = os.getenv("DB_USERNAME", "dev")
    password = os.getenv("DB_PASSWORD", "dev")
    db = os.getenv("DB_NAME", "entity_dev")
    dsn = f"postgresql://{user}:{password}@{docker_ip}:{port}/{db}"
    print(f"✅ Returning test Postgres DSN: {dsn}")

    async def check():
        return await _can_connect(dsn)

    docker_services.wait_until_responsive(
        timeout=30, pause=0.5, check=lambda: asyncio.run(check())
    )
    return dsn


class AsyncPGDatabase(DatabaseResource):
    def __init__(self, dsn: str):
        super().__init__({})
        self._dsn = dsn

    @asynccontextmanager
    async def connection(self):
        parsed = urlparse(self._dsn)
        host = parsed.hostname
        port = parsed.port

        wait_for_port(host, port)
        conn = await asyncpg.connect(self._dsn)
        try:
            yield conn
        finally:
            await conn.close()

    def get_connection_pool(self):
        return self._dsn


@pytest.fixture(scope="session")
async def pg_memory(postgres_dsn: str) -> Memory:
    _require_docker()
    db = AsyncPGDatabase(postgres_dsn)
    mem = Memory({})
    mem.database = db
    mem.vector_store = None
    await mem.initialize()
    try:
        yield mem
    finally:
        async with db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")


@pytest.fixture(scope="session")
def ollama_url(docker_ip: str, docker_services) -> str:
    """Ensure Ollama container is healthy and return its base URL."""
    _require_docker()
    port = docker_services.port_for("ollama", OLLAMA_PORT)
    base_url = f"http://{docker_ip}:{port}"

    def is_responsive() -> bool:
        import httpx

        try:
            # Ping Ollama with a fake model — 404 is okay, means service is up
            response = httpx.post(
                f"{base_url}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": "ping"},
                timeout=2.0,
            )
            return response.status_code in {200, 400, 404}
        except Exception:
            return False

    docker_services.wait_until_responsive(timeout=60, pause=1.0, check=is_responsive)
    return base_url


@pytest.fixture(scope="session")
async def ollama_llm(ollama_url: str) -> LLM:
    """LLM using Ollama container."""
    from plugins.builtin.resources.ollama_llm import OllamaLLMResource

    llm_provider = OllamaLLMResource({"base_url": ollama_url, "model": OLLAMA_MODEL})
    llm = LLM({"pool": {"min_size": 1, "max_size": 1}})
    llm.provider = llm_provider
    await llm.initialize()
    yield llm


@pytest.fixture()
async def memory_db(tmp_path: Path) -> Memory:
    """Isolated DuckDB-backed memory."""
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
