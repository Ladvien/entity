class DuckDBInfrastructure:
    """Layer 1 infrastructure for managing a DuckDB database file."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self._connection = None

    def connect(self):
        """Return an open DuckDB connection."""
        import duckdb

        if self._connection is None:
            self._connection = duckdb.connect(self.file_path)
        return self._connection
