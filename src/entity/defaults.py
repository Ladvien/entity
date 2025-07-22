"""Convenience constructors for Layer 0 defaults."""

from __future__ import annotations

from .infrastructure.duckdb_infra import DuckDBInfrastructure
from .infrastructure.ollama_infra import OllamaInfrastructure
from .infrastructure.local_storage_infra import LocalStorageInfrastructure
from .resources import (
    DatabaseResource,
    VectorStoreResource,
    LLMResource,
    Memory,
    LLM,
    LocalStorageResource,
    Storage,
)


# Default infrastructure instances
DUCKDB = DuckDBInfrastructure("./agent_memory.duckdb")
OLLAMA = OllamaInfrastructure("http://localhost:11434", "llama3.2:3b")
LOCAL_STORAGE = LocalStorageInfrastructure("./agent_files")


def load_defaults() -> dict[str, object]:
    """Return canonical Layer-3 resources configured with default infrastructure."""

    db_resource = DatabaseResource(DUCKDB)
    vector_resource = VectorStoreResource(DUCKDB)
    llm_resource = LLMResource(OLLAMA)
    storage_resource = LocalStorageResource(LOCAL_STORAGE)

    return {
        "memory": Memory(db_resource, vector_resource),
        "llm": LLM(llm_resource),
        "storage": Storage(storage_resource),
    }
