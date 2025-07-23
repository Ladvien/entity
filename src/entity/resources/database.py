"""Database resource that executes queries using a DuckDB backend."""

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


class DatabaseResource:
    """Layer 2 resource providing database access."""

    def __init__(self, infrastructure: DuckDBInfrastructure) -> None:
        """Initialize with an injected DuckDB infrastructure."""

        self.infrastructure = infrastructure

    def execute(self, query: str, *params: object) -> object:
        """Execute a SQL query and return the result cursor."""

        conn = self.infrastructure.connect()
        return conn.execute(query, params)
