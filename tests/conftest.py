import os
import sys
import asyncio
import socket
import shutil
import subprocess
import time
from pathlib import Path
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import asyncpg
from pgvector.asyncpg import register_vector
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# -- Pytest-docker sanity check
REQUIRE_PYTEST_DOCKER = (
    "pytest-docker is required. Run 'poetry install --with dev' to install it."
)

try:
    import pytest_docker as _  # noqa: F401

    PYTEST_DOCKER_AVAILABLE = True
except Exception:
    PYTEST_DOCKER_AVAILABLE = False

DOCKER_INSTALLED = shutil.which("docker") is not None

# -- Path setup
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("ENTITY_AUTO_INIT", "0")

# -- Constants
OLLAMA_PORT = int(os.getenv("OLLAMA_PORT", "11434"))
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q6_K")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", f"http://localhost:{OLLAMA_PORT}")
POSTGRES_READY_TIMEOUT = int(os.getenv("POSTGRES_READY_TIMEOUT", "180"))
OLLAMA_READY_TIMEOUT = int(os.getenv("OLLAMA_READY_TIMEOUT", "180"))

from entity.infrastructure import DuckDBInfrastructure, AsyncPGInfrastructure
from entity.resources import Memory, LLM
from plugins.builtin.resources.pg_vector_store import PgVectorStore
from entity.resources.database import DuckDBResource, DatabaseResource
from entity.core.resources.container import ResourceContainer


def _require_docker() -> bool:
    """Return True if Docker tooling is available and running."""
    if not PYTEST_DOCKER_AVAILABLE or not DOCKER_INSTALLED:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return False
    return True


def wait_for_port(host: str, port: int, timeout: float = 30.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"Timeout waiting for {host}:{port}")


async def _can_connect(dsn: str) -> bool:
    try:
        conn = await asyncpg.connect(dsn)
        await conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_dsn(docker_ip: str, docker_services) -> str:
    if not _require_docker():
        pytest.skip("Docker is required for Postgres fixtures.")
    port = docker_services.port_for("postgres", 5432)
    dsn = f"postgresql://{os.getenv('DB_USERNAME', 'dev')}:{os.getenv('DB_PASSWORD', 'dev')}@{docker_ip}:{port}/{os.getenv('DB_NAME', 'entity_dev')}"
    print(f"✅ Returning test Postgres DSN: {dsn}")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    def check():
        return loop.run_until_complete(_can_connect(dsn))

    try:
        docker_services.wait_until_responsive(
            timeout=POSTGRES_READY_TIMEOUT, pause=0.5, check=check
        )
    except Exception:
        try:
            print("\n❌ Postgres container logs:\n" + docker_services.logs("postgres"))
        except Exception as log_error:
            print(f"Failed to retrieve postgres logs: {log_error}")
        raise
    return dsn


class AsyncPGDatabase(DatabaseResource):
    def __init__(self, dsn: str) -> None:
        super().__init__({})
        self._dsn = dsn
        self.database = None

    @classmethod
    def from_config(cls, cfg: dict) -> "AsyncPGDatabase":
        return cls(cfg["dsn"])

    @asynccontextmanager
    async def connection(self):
        backend = getattr(self, "database", None)
        if backend is None:
            parsed = urlparse(self._dsn)
            wait_for_port(parsed.hostname, parsed.port)
            conn = await asyncpg.connect(self._dsn)
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await register_vector(conn)
            try:
                yield conn
            finally:
                await conn.close()
        else:
            async with backend.connection() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await register_vector(conn)
                yield conn

    def get_connection_pool(self):
        backend = getattr(self, "database", None)
        if backend is not None:
            return backend.get_connection_pool()
        return self._dsn


@pytest.fixture(scope="function")
async def pg_memory(postgres_dsn: str) -> Memory:
    if not _require_docker():
        pytest.skip("Docker is required for PostgreSQL-backed memory.")
    db = AsyncPGDatabase(postgres_dsn)
    mem = Memory({})
    mem.database = db
    await mem.initialize()
    try:
        yield mem
    finally:
        async with db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")


@pytest.fixture(scope="function")
async def pg_vector_memory(postgres_dsn: str) -> Memory:
    if not _require_docker():
        pytest.skip("Docker is required for PostgreSQL-backed memory.")
    db = AsyncPGDatabase(postgres_dsn)
    store = PgVectorStore({"table": "test_embeddings"})
    store.database = db
    mem = Memory({})
    mem.database = db
    mem.vector_store = store
    await store.initialize()
    await mem.initialize()
    try:
        yield mem
    finally:
        async with db.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {mem._kv_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {mem._history_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {store._table}")


@pytest.fixture()
async def clear_pg_memory(pg_memory):
    async with pg_memory.database.connection() as conn:
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {pg_memory._kv_table} (
                key TEXT PRIMARY KEY,
                value JSONB
            )
        """
        )
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {pg_memory._history_table} (
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                metadata JSONB,
                timestamp TIMESTAMPTZ
            )
        """
        )
        await conn.execute(f"DELETE FROM {pg_memory._kv_table}")
        await conn.execute(f"DELETE FROM {pg_memory._history_table}")
    yield


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig: pytest.Config) -> str:
    if not _require_docker():
        pytest.skip("Docker is required for docker-compose fixtures.")
    return str(Path(pytestconfig.rootpath) / "tests" / "docker-compose.yml")


@pytest.fixture(scope="session")
def ollama_url(docker_ip: str, docker_services) -> str:
    if not _require_docker():
        pytest.skip("Docker is required for Ollama LLM tests.")
    port = docker_services.port_for("ollama", OLLAMA_PORT)
    base_url = f"http://{docker_ip}:{port}"

    def is_responsive() -> bool:
        import httpx

        try:
            response = httpx.post(
                f"{base_url}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": "ping"},
                timeout=2.0,
            )
            return response.status_code in {200, 400, 404}
        except Exception:
            return False

    docker_services.wait_until_responsive(
        timeout=OLLAMA_READY_TIMEOUT, pause=1.0, check=is_responsive
    )
    return base_url


@pytest.fixture(scope="session")
async def ollama_llm(ollama_url: str) -> LLM:
    from plugins.builtin.resources.ollama_llm import OllamaLLMResource

    llm_provider = OllamaLLMResource({"base_url": ollama_url, "model": OLLAMA_MODEL})
    llm = LLM({"pool": {"min_size": 1, "max_size": 1}})
    llm.provider = llm_provider
    await llm.initialize()
    yield llm


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


@pytest.fixture()
async def pg_container(postgres_dsn: str) -> ResourceContainer:
    if not _require_docker():
        pytest.skip("Docker is required for Postgres-backed containers.")
    container = ResourceContainer()
    container.register(
        "database_backend",
        AsyncPGInfrastructure,
        {"dsn": postgres_dsn},
        layer=1,
    )
    container.register(
        "database",
        AsyncPGDatabase,
        {"dsn": postgres_dsn},
        layer=2,
    )
    container.register("memory", Memory, {}, layer=3)

    await container.build_all()
    try:
        yield container
    finally:
        memory = container.get("memory")
        assert memory is not None
        async with memory.database.connection() as conn:
            await conn.execute(f"DROP TABLE IF EXISTS {memory._kv_table}")
            await conn.execute(f"DROP TABLE IF EXISTS {memory._history_table}")
        await container.shutdown_all()


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
