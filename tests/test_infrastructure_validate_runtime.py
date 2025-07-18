import pytest

from entity.core.resources.container import ResourceContainer
from tests.infrastructure import (
    FailingDuckDBInfrastructure,
    FailingPostgresInfrastructure,
)


@pytest.mark.asyncio
async def test_duckdb_runtime_breaker_opens():
    container = ResourceContainer()
    container.register(
        "duckdb",
        FailingDuckDBInfrastructure,
        {"failure_threshold": 2},
        layer=1,
    )
    await container.build_all()
    db = container.get("duckdb")
    res1 = await db.validate_runtime()
    assert not res1.success
    assert "boom" in res1.message

    res2 = await db.validate_runtime()
    assert not res2.success

    res3 = await db.validate_runtime()
    assert not res3.success

    await container.shutdown_all()


@pytest.mark.asyncio
async def test_postgres_runtime_breaker_opens():
    container = ResourceContainer()
    container.register(
        "postgres",
        FailingPostgresInfrastructure,
        {"failure_threshold": 2},
        layer=1,
    )
    await container.build_all()
    pg = container.get("postgres")
    res1 = await pg.validate_runtime()
    assert not res1.success
    assert "bad" in res1.message

    res2 = await pg.validate_runtime()
    assert not res2.success

    res3 = await pg.validate_runtime()
    assert not res3.success

    await container.shutdown_all()
