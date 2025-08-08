"""Vector store resource backed by DuckDB."""

from entity.infrastructure.protocols import VectorStoreInfrastructure
from entity.resources.exceptions import ResourceInitializationError


class VectorStoreResource:
    """Layer 2 resource for storing and searching vectors."""

    def __init__(self, infrastructure: VectorStoreInfrastructure | None) -> None:
        """Create the resource with a vector store backend."""

        if infrastructure is None:
            raise ResourceInitializationError("VectorStoreInfrastructure is required")
        self.infrastructure = infrastructure

    async def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return await self.infrastructure.health_check()
    
    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check for compatibility."""
        return self.infrastructure.health_check_sync()

    def add_vector(self, table: str, vector: object) -> None:
        """Insert a vector into the given table."""
        
        # Validate table name to prevent SQL injection
        if not table.isidentifier():
            raise ValueError(f"Invalid table name: {table}")
        
        # Create table if it doesn't exist
        with self.infrastructure.connect() as conn:
            # Use parameterized query for the vector value, table name is validated
            conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (vector ANY)")
            conn.execute(f"INSERT INTO {table} VALUES (?)", (vector,))

    def query(self, query: str) -> object:
        """Run a vector search query."""

        with self.infrastructure.connect() as conn:
            return conn.execute(query)
