from .database import DatabaseResource
from .vector_store import VectorStoreResource
from .exceptions import ResourceInitializationError


class Memory:
    """Layer 3 resource that exposes persistent memory capabilities."""

    def __init__(
        self,
        database: DatabaseResource | None,
        vector_store: VectorStoreResource | None,
    ) -> None:
        if database is None or vector_store is None:
            raise ResourceInitializationError(
                "DatabaseResource and VectorStoreResource are required"
            )
        self.database = database
        self.vector_store = vector_store

    def execute(self, query: str, *params):
        return self.database.execute(query, *params)

    def add_vector(self, table: str, vector):
        self.vector_store.add_vector(table, vector)

    def query(self, query: str):
        return self.vector_store.query(query)
