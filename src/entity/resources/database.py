"""Database resource that executes queries using a DuckDB backend."""

from entity.infrastructure.protocols import DatabaseInfrastructure
from entity.resources.exceptions import ResourceInitializationError


class DatabaseResource:
    """Layer 2 resource providing database access."""

    def __init__(self, infrastructure: DatabaseInfrastructure | None) -> None:
        """Initialize with an injected database infrastructure."""

        if infrastructure is None:
            raise ResourceInitializationError("DatabaseInfrastructure is required")
        self.infrastructure = infrastructure

    async def health_check(self) -> bool:
        """Return ``True`` if the underlying infrastructure is healthy."""

        return await self.infrastructure.health_check()
    
    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check for compatibility."""
        return self.infrastructure.health_check_sync()

    def execute(self, query: str, *params: object) -> object:
        """Execute a SQL query and return the result cursor."""

        with self.infrastructure.connect() as conn:
            return conn.execute(query, params)
