"""Database resource that executes queries using a DuckDB backend."""

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.resources.exceptions import ResourceInitializationError


class DatabaseResource:
    """Layer 2 resource providing database access."""

    def __init__(self, infrastructure: DuckDBInfrastructure | None) -> None:
        """Initialize with an injected DuckDB infrastructure."""

        if infrastructure is None:
            raise ResourceInitializationError("DuckDBInfrastructure is required")
        self.infrastructure = infrastructure

    def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return self.infrastructure.health_check()

    def execute(self, query: str, *params: object) -> object:
        """Execute a SQL query and return the result cursor."""

        with self.infrastructure.connect() as conn:
            return conn.execute(query, params)
