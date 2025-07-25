from __future__ import annotations

import os
import tempfile
import logging
from dataclasses import dataclass

# TODO: Do not use relative imports
from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure
from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure
from entity.infrastructure.ollama_installer import OllamaInstaller
from entity.resources import (
    DatabaseResource,
    VectorStoreResource,
    LLMResource,
    Memory,
    LLM,
    LocalStorageResource,
    Storage,
)


# TODO: Should be using Pydantic BaseModel or similar
@dataclass
class DefaultConfig:
    """Configuration values for default resources."""

    duckdb_path: str = "./agent_memory.duckdb"
    # TODO: Port should be configurable
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    storage_path: str = "./agent_files"

    @classmethod
    def from_env(cls) -> "DefaultConfig":
        """Create config overriding fields with environment variables."""

        return cls(
            duckdb_path=os.getenv("ENTITY_DUCKDB_PATH", cls.duckdb_path),
            ollama_url=os.getenv("ENTITY_OLLAMA_URL", cls.ollama_url),
            ollama_model=os.getenv("ENTITY_OLLAMA_MODEL", cls.ollama_model),
            storage_path=os.getenv("ENTITY_STORAGE_PATH", cls.storage_path),
        )


class _NullLLMInfrastructure:
    """Fallback LLM implementation used when Ollama is unavailable."""

    def generate(self, prompt: str) -> str:  # pragma: no cover - simple stub
        return "LLM service unavailable"

    def health_check(self) -> bool:  # pragma: no cover - constant result
        return False


# TODO: Please use OOP
def load_defaults(config: DefaultConfig | None = None) -> dict[str, object]:
    """Build canonical resources using ``config`` or environment overrides."""

    cfg = config or DefaultConfig.from_env()
    logger = logging.getLogger("defaults")

    duckdb = DuckDBInfrastructure(cfg.duckdb_path)
    if not duckdb.health_check():
        logger.debug("Falling back to in-memory DuckDB")
        duckdb = DuckDBInfrastructure(":memory:")

    ollama = OllamaInfrastructure(cfg.ollama_url, cfg.ollama_model)
    logger.debug("Checking local Ollama at %s", cfg.ollama_url)
    if not ollama.health_check():
        logger.debug("Ollama not reachable; attempting installation")
        OllamaInstaller.ensure_installed()
        if not ollama.health_check():
            logger.warning("Using stub LLM implementation")
            ollama = _NullLLMInfrastructure()

    storage_infra = LocalStorageInfrastructure(cfg.storage_path)
    if not storage_infra.health_check():
        fallback = os.path.join(tempfile.gettempdir(), "entity_files")
        logger.warning(
            "Storage path %s unavailable; falling back to %s",
            cfg.storage_path,
            fallback,
        )
        storage_infra = LocalStorageInfrastructure(fallback)

    db_resource = DatabaseResource(duckdb)
    vector_resource = VectorStoreResource(duckdb)
    llm_resource = LLMResource(ollama)
    storage_resource = LocalStorageResource(storage_infra)

    return {
        "memory": Memory(db_resource, vector_resource),
        "llm": LLM(llm_resource),
        "storage": Storage(storage_resource),
    }
