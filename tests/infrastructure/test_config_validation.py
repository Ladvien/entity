import pytest

from entity.infrastructure import (
    PostgresInfrastructure,
    AsyncPGInfrastructure,
    DuckDBInfrastructure,
    DockerInfrastructure,
    LlamaCppInfrastructure,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cls,config",
    [
        (PostgresInfrastructure, {"dsn": "postgresql://user@localhost/db"}),
        (AsyncPGInfrastructure, {"dsn": "postgresql://user@localhost/db"}),
        (DuckDBInfrastructure, {"path": ":memory:"}),
        (DockerInfrastructure, {"path": "."}),
        (LlamaCppInfrastructure, {"model": "model.bin"}),
    ],
)
async def test_validate_config_valid(cls, config):
    result = await cls.validate_config(config)
    assert result.success


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cls,config",
    [
        (PostgresInfrastructure, {"dsn": 1}),
        (AsyncPGInfrastructure, {"dsn": 1}),
        (DuckDBInfrastructure, {"path": 2}),
        (DockerInfrastructure, {"path": 3}),
        (LlamaCppInfrastructure, {"model": "x", "port": "bad"}),
    ],
)
async def test_validate_config_invalid(cls, config):
    result = await cls.validate_config(config)
    assert not result.success
