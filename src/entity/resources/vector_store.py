"""Vector store resource backed by DuckDB."""

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure


class VectorStoreResource:
    """Layer 2 resource for storing and searching vectors."""

    def __init__(self, infrastructure: DuckDBInfrastructure) -> None:
        """Create the resource with a DuckDB backend."""

        self.infrastructure = infrastructure

    def add_vector(self, table: str, vector: object) -> None:
        """Insert a vector into the given table."""

        conn = self.infrastructure.connect()
        conn.execute(f"INSERT INTO {table} VALUES (?)", (vector,))

    def query(self, query: str) -> object:
        """Run a vector search query."""

        conn = self.infrastructure.connect()
        return conn.execute(query)
