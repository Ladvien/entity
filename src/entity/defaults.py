import os
import tempfile
import logging
from dataclasses import dataclass

from entity.infrastructure.duckdb_infra import DuckDBInfrastructure
from entity.infrastructure.ollama_infra import OllamaInfrastructure
from entity.infrastructure.vllm_infra import VLLMInfrastructure
from entity.infrastructure.local_storage_infra import LocalStorageInfrastructure
from entity.setup.ollama_installer import OllamaInstaller
from entity.setup.vllm_installer import VLLMInstaller
from entity.resources import (
    DatabaseResource,
    VectorStoreResource,
    LLMResource,
    Memory,
    LLM,
    LocalStorageResource,
    FileStorage,
    RichLoggingResource,
    LogLevel,
)
from entity.resources.exceptions import InfrastructureError


@dataclass
class DefaultConfig:
    """Configuration values for default resources."""

    duckdb_path: str = "./agent_memory.duckdb"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    storage_path: str = "./agent_files"
    auto_install_ollama: bool = True
    auto_install_vllm: bool = True
    vllm_model: str | None = None

    @classmethod
    def from_env(cls) -> "DefaultConfig":
        """Create config overriding fields with environment variables."""

        return cls(
            duckdb_path=os.getenv("ENTITY_DUCKDB_PATH", cls.duckdb_path),
            storage_path=os.getenv("ENTITY_STORAGE_PATH", cls.storage_path),
            auto_install_vllm=os.getenv(
                "ENTITY_AUTO_INSTALL_VLLM",
                str(cls.auto_install_vllm),
            ).lower()
            in {"1", "true", "yes"},
            vllm_model=os.getenv("ENTITY_VLLM_MODEL", cls.vllm_model),
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

    llm_infra = None

    # Try vLLM first (primary default)
    try:
        VLLMInstaller.ensure_vllm_available()
        vllm_infra = VLLMInfrastructure(auto_detect_model=True)
        if vllm_infra.health_check():
            llm_infra = vllm_infra
            logger.info("Using vLLM with auto-detected model: %s", vllm_infra.model)
        else:
            raise InfrastructureError("vLLM setup failed")
    except Exception as exc:
        logger.warning("vLLM setup failed, falling back to Ollama: %s", exc)
        # Fallback to Ollama logic here
        try:
            ollama_infra = OllamaInfrastructure(cfg.ollama_url, cfg.ollama_model)
            if ollama_infra.health_check():
                llm_infra = ollama_infra
            else:
                raise InfrastructureError("Both vLLM and Ollama unavailable")
        except Exception:
            raise InfrastructureError("No LLM infrastructure available")

    duckdb = DuckDBInfrastructure(cfg.duckdb_path)
    if not duckdb.health_check():
        logger.debug("Falling back to in-memory DuckDB")
        duckdb = DuckDBInfrastructure(":memory:")

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
    llm_resource = LLMResource(llm_infra)
    storage_resource = LocalStorageResource(storage_infra)

    return {
        "memory": Memory(db_resource, vector_resource),
        "llm": LLM(llm_resource),
        "file_storage": FileStorage(storage_resource),
        "logging": logging_resource,
    }
