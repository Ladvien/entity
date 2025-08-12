import logging
import os
import tempfile
from dataclasses import dataclass

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure
from entity.resources import (
    LLM,
    DatabaseResource,
    FileStorage,
    LLMResource,
    LocalStorageResource,
    LogLevel,
    Memory,
    RichLoggingResource,
    VectorStoreResource,
    create_argument_parsing_resource,
)
from entity.resources.exceptions import InfrastructureError
from entity.setup.ollama_installer import OllamaInstaller


@dataclass
class DefaultConfig:
    """Configuration values for default resources."""

    duckdb_path: str = "./agent_memory.duckdb"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    storage_path: str = "./agent_files"
    auto_install_ollama: bool = True

    @classmethod
    def from_env(cls) -> "DefaultConfig":
        """Create config overriding fields with environment variables."""

        return cls(
            duckdb_path=os.getenv("ENTITY_DUCKDB_PATH", cls.duckdb_path),
            storage_path=os.getenv("ENTITY_STORAGE_PATH", cls.storage_path),
            ollama_url=os.getenv("ENTITY_OLLAMA_URL", cls.ollama_url),
            ollama_model=os.getenv("ENTITY_OLLAMA_MODEL", cls.ollama_model),
            auto_install_ollama=os.getenv(
                "ENTITY_AUTO_INSTALL_OLLAMA",
                str(cls.auto_install_ollama),
            ).lower()
            in {"1", "true", "yes"},
        )


def load_defaults(config: DefaultConfig | None = None) -> dict[str, object]:
    """Build canonical resources using ``config`` or environment overrides."""

    cfg = config or DefaultConfig.from_env()
    logger = logging.getLogger("defaults")

    log_level = LogLevel(os.getenv("ENTITY_LOG_LEVEL", "info"))
    json_logs = os.getenv("ENTITY_JSON_LOGS", "0").lower() in {"1", "true", "yes"}
    log_file = os.getenv("ENTITY_LOG_FILE", "./agent.log")
    logging_resource = RichLoggingResource(
        level=log_level,
        json=json_logs,
        log_file=log_file,
    )

    try:
        if cfg.auto_install_ollama:
            OllamaInstaller.ensure_ollama_available(cfg.ollama_model)
        ollama_infra = OllamaInfrastructure(cfg.ollama_url, cfg.ollama_model)
        if ollama_infra.health_check_sync():
            llm_infra = ollama_infra
            logger.info("Using Ollama with model: %s", cfg.ollama_model)
        else:
            raise InfrastructureError("Ollama unavailable")
    except Exception as exc:
        raise InfrastructureError(f"No LLM infrastructure available: {exc}")

    duckdb = DuckDBInfrastructure(cfg.duckdb_path)
    if not duckdb.health_check_sync():
        logger.debug("Falling back to in-memory DuckDB")
        duckdb = DuckDBInfrastructure(":memory:")

    storage_infra = LocalStorageInfrastructure(cfg.storage_path)
    if not storage_infra.health_check_sync():
        fallback = os.path.join(tempfile.gettempdir(), "entity_files")
        logger.warning(
            "Storage path %s unavailable; falling back to %s",
            cfg.storage_path,
            fallback,
        )
        storage_infra = LocalStorageInfrastructure(fallback)

    db_resource = DatabaseResource(duckdb)
    vector_resource = VectorStoreResource(duckdb)
    llm_resource = LLMResource(llm_infra)
    storage_resource = LocalStorageResource(storage_infra)

    argument_parsing_resource = create_argument_parsing_resource(
        logger=logging_resource,
        app_name="entity-cli",
        app_description="Entity Framework - Build powerful AI agents",
    )

    return {
        "memory": Memory(db_resource, vector_resource),
        "llm": LLM(llm_resource),
        "file_storage": FileStorage(storage_resource),
        "logging": logging_resource,
        "argument_parsing": argument_parsing_resource,
    }
