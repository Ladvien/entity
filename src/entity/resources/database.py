from ..infrastructure.duckdb_infra import DuckDBInfrastructure


class DatabaseResource:
    """Layer 2 resource providing database access."""

    def __init__(self, infrastructure: DuckDBInfrastructure) -> None:
        self.infrastructure = infrastructure

    def execute(self, query: str, *params):
        conn = self.infrastructure.connect()
        return conn.execute(query, params)
