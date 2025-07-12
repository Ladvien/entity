import pytest

from entity.infrastructure import DuckDBInfrastructure, PostgresInfrastructure
from pipeline.exceptions import CircuitBreakerTripped


@pytest.mark.asyncio
async def test_duckdb_runtime_breaker_opens(monkeypatch):
    db = DuckDBInfrastructure({"failure_threshold": 2})

    class BadConn:
        def execute(self, _q):
            raise RuntimeError("boom")

        def close(self):
            pass

    db._conn = BadConn()

    res1 = await db.validate_runtime()
    assert not res1.success
    assert "boom" in res1.message

    res2 = await db.validate_runtime()
    assert not res2.success

    res3 = await db.validate_runtime()
    assert not res3.success
    assert "circuit breaker open" in res3.message.lower()


@pytest.mark.asyncio
async def test_postgres_runtime_breaker_opens(monkeypatch):
    pg = PostgresInfrastructure({"failure_threshold": 2})

    class BadConn:
        async def execute(self, *_args, **_kwargs):
            raise RuntimeError("bad")

    async def acquire():
        return BadConn()

    pg._pool.acquire = acquire

    res1 = await pg.validate_runtime()
    assert not res1.success
    assert "bad" in res1.message

    res2 = await pg.validate_runtime()
    assert not res2.success

    res3 = await pg.validate_runtime()
    assert not res3.success
    assert "circuit breaker open" in res3.message.lower()
