from ..infrastructure.duckdb_infra import DuckDBInfrastructure


class VectorStoreResource:
    """Layer 2 resource for storing and searching vectors."""

    def __init__(self, infrastructure: DuckDBInfrastructure) -> None:
        self.infrastructure = infrastructure

    def add_vector(self, table: str, vector):
        conn = self.infrastructure.connect()
        conn.execute(f"INSERT INTO {table} VALUES (?)", (vector,))

    def query(self, query: str):
        conn = self.infrastructure.connect()
        return conn.execute(query)
