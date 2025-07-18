from entity.infrastructure.docker import DockerInfrastructure
from entity.infrastructure.duckdb import DuckDBInfrastructure
from entity.infrastructure.llamacpp import LlamaCppInfrastructure
from entity.infrastructure.postgres import PostgresInfrastructure


def test_infrastructure_plugins_have_no_dependencies() -> None:
    classes = [
        DockerInfrastructure,
        DuckDBInfrastructure,
        LlamaCppInfrastructure,
        PostgresInfrastructure,
    ]
    for cls in classes:
        assert (
            getattr(cls, "dependencies", []) == []
        ), f"{cls.__name__} declares dependencies"
        assert (
            "dependencies" in cls.__dict__
        ), f"{cls.__name__} missing dependencies attribute"
