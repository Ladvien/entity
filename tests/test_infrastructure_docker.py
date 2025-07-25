import shutil
import pytest

from entity.infrastructure import (
    DuckDBInfrastructure,
    LocalStorageInfrastructure,
    OllamaInfrastructure,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_duckdb_startup_shutdown(tmp_path):
    infra = DuckDBInfrastructure(str(tmp_path / "db.duckdb"))
    await infra.startup()
    assert infra.health_check()
    await infra.shutdown()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_local_storage_startup_shutdown(tmp_path):
    infra = LocalStorageInfrastructure(tmp_path)
    await infra.startup()
    assert infra.health_check()
    await infra.shutdown()


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not installed")
@pytest.mark.asyncio
async def test_ollama_health(compose_services):
    infra = OllamaInfrastructure("http://localhost:11434", "test")
    await infra.startup()
    try:
        assert infra.health_check()
    finally:
        await infra.shutdown()
