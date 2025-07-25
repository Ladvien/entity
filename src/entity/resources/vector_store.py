"""Vector store resource backed by DuckDB."""

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.resources.exceptions import ResourceInitializationError


class VectorStoreResource:
    """Layer 2 resource for storing and searching vectors."""

    def __init__(self, infrastructure: DuckDBInfrastructure | None) -> None:
        """Create the resource with a DuckDB backend."""

        if infrastructure is None:
            raise ResourceInitializationError("DuckDBInfrastructure is required")
        self.infrastructure = infrastructure

    def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return self.infrastructure.health_check()

    def add_vector(self, table: str, vector: object) -> None:
        """Insert a vector into the given table."""

        with self.infrastructure.connect() as conn:
            conn.execute(f"INSERT INTO {table} VALUES (?)", (vector,))

    def query(self, query: str) -> object:
        """Run a vector search query."""

        with self.infrastructure.connect() as conn:
            return conn.execute(query)
