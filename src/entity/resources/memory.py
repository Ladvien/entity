from entity.resources.database import DatabaseResource
from entity.resources.vector_store import VectorStoreResource
from entity.resources.exceptions import ResourceInitializationError


class Memory:
    """Layer 3 resource that exposes persistent memory capabilities."""

    def __init__(
        self,
        database: DatabaseResource | None,
        vector_store: VectorStoreResource | None,
    ) -> None:
        """Create the memory wrapper with required resources."""

        if database is None or vector_store is None:
            raise ResourceInitializationError(
                "DatabaseResource and VectorStoreResource are required"
            )
        self.database = database
        self.vector_store = vector_store

    def execute(self, query: str, *params: object) -> object:
        """Execute a database query."""

        return self.database.execute(query, *params)

    def add_vector(self, table: str, vector: object) -> None:
        """Store a vector via the underlying vector resource."""

        self.vector_store.add_vector(table, vector)

    def query(self, query: str) -> object:
        """Execute a vector store query."""

        return self.vector_store.query(query)
