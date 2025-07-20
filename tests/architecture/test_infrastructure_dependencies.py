from entity.infrastructure.docker import DockerInfrastructure
from entity.infrastructure.duckdb import DuckDBInfrastructure
from entity.infrastructure.llamacpp import LlamaCppInfrastructure
from entity.infrastructure.postgres import PostgresInfrastructure
from entity.infrastructure.duckdb_vector import DuckDBVectorInfrastructure
from entity.resources.duckdb_vector_store import DuckDBVectorStore
from entity.resources.vector_store import VectorStoreResource


def test_infrastructure_plugins_have_no_dependencies() -> None:
    classes = [
        DockerInfrastructure,
        DuckDBInfrastructure,
        LlamaCppInfrastructure,
        PostgresInfrastructure,
        DuckDBVectorInfrastructure,
    ]
    for cls in classes:
        assert (
            getattr(cls, "dependencies", []) == []
        ), f"{cls.__name__} declares dependencies"
        assert (
            "dependencies" in cls.__dict__
        ), f"{cls.__name__} missing dependencies attribute"


def test_vector_store_resource_requires_backend() -> None:
    assert DuckDBVectorStore.infrastructure_dependencies == ["vector_store_backend"]


def test_vector_store_interface_dependency() -> None:
    assert VectorStoreResource.infrastructure_dependencies == ["vector_store"]
