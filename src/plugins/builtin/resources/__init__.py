"""Resource implementations shipped with the framework."""

from entity.resources.interfaces.echo_llm import EchoLLMResource
from entity.resources.interfaces.ollama_llm import OllamaLLMResource
from entity.resources.interfaces.pg_vector_store import PgVectorStore
from entity.resources.interfaces.duckdb_resource import DuckDBResource

__all__ = [
    "EchoLLMResource",
    "OllamaLLMResource",
    "PgVectorStore",
    "DuckDBResource",
]
