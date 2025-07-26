from __future__ import annotations

import os
import tempfile
import logging
from dataclasses import dataclass

# TODO: Do not use relative imports
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
    Storage,
    ConsoleLoggingResource,
    JSONLoggingResource,
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
    auto_install_ollama: bool = True
    auto_install_vllm: bool = True
<<<<<<< HEAD
=======
    vllm_model: str | None = None
>>>>>>> pr-1954

    @classmethod
    def from_env(cls) -> "DefaultConfig":
        """Create config overriding fields with environment variables."""

        return cls(
            duckdb_path=os.getenv("ENTITY_DUCKDB_PATH", cls.duckdb_path),
            ollama_url=os.getenv("ENTITY_OLLAMA_URL", cls.ollama_url),
            ollama_model=os.getenv("ENTITY_OLLAMA_MODEL", cls.ollama_model),
            storage_path=os.getenv("ENTITY_STORAGE_PATH", cls.storage_path),
            auto_install_ollama=os.getenv(
                "ENTITY_AUTO_INSTALL_OLLAMA",
                str(cls.auto_install_ollama),
            ).lower()
            in {"1", "true", "yes"},
            auto_install_vllm=os.getenv(
                "ENTITY_AUTO_INSTALL_VLLM",
                str(cls.auto_install_vllm),
            ).lower()
            in {"1", "true", "yes"},
<<<<<<< HEAD
=======
            vllm_model=os.getenv("ENTITY_VLLM_MODEL", cls.vllm_model),
>>>>>>> pr-1954
        )


class _NullLLMInfrastructure:
    """Fallback LLM implementation used when Ollama is unavailable."""

    async def generate(self, prompt: str) -> str:  # pragma: no cover - simple stub
        return "LLM service unavailable"

    def health_check(self) -> bool:  # pragma: no cover - constant result
        return False


# TODO: Please use OOP
def load_defaults(config: DefaultConfig | None = None) -> dict[str, object]:
    """Build canonical resources using ``config`` or environment overrides."""

    cfg = config or DefaultConfig.from_env()
    logger = logging.getLogger("defaults")

<<<<<<< HEAD
<<<<<<< HEAD
    log_level = os.getenv("ENTITY_LOG_LEVEL", "info")
    json_logs = os.getenv("ENTITY_JSON_LOGS", "0").lower() in {"1", "true", "yes"}
    log_file = os.getenv("ENTITY_LOG_FILE", "./agent.log")
    logging_resource = (
        JSONLoggingResource(log_file, log_level)
        if json_logs
        else ConsoleLoggingResource(log_level)
    )

    if cfg.auto_install_ollama:
        OllamaInstaller.ensure_ollama_available(cfg.ollama_model)
=======
    llm_impl: object | None = None

    if cfg.auto_install_vllm:
        try:
            VLLMInstaller.ensure_vllm_available()
            vllm = VLLMInfrastructure()
            if vllm.health_check():
                llm_impl = vllm
                logger.info("Using vLLM as default LLM")
        except Exception as exc:  # pragma: no cover - setup issues
            logger.warning("vLLM setup failed: %s", exc)

    if llm_impl is None:
        if cfg.auto_install_ollama:
            OllamaInstaller.ensure_ollama_available(cfg.ollama_model)
>>>>>>> pr-1950
=======
    llm_infra = None

    if cfg.auto_install_vllm:
        try:
            VLLMInstaller.ensure_vllm_available(cfg.vllm_model)
            vllm = VLLMInfrastructure(model=cfg.vllm_model)
            logger.debug("Checking local vLLM at %s", vllm.base_url)
            if vllm.health_check():
                llm_infra = vllm
                logger.info("Using vLLM infrastructure")
        except Exception as exc:
            logger.warning("vLLM setup failed: %s", exc)

    if llm_infra is None:
        if cfg.auto_install_ollama:
            OllamaInstaller.ensure_ollama_available(cfg.ollama_model)
>>>>>>> pr-1954

    duckdb = DuckDBInfrastructure(cfg.duckdb_path)
    if not duckdb.health_check():
        logger.debug("Falling back to in-memory DuckDB")
        duckdb = DuckDBInfrastructure(":memory:")

<<<<<<< HEAD
    if llm_impl is None:
=======
    if llm_infra is None:
>>>>>>> pr-1954
        ollama = OllamaInfrastructure(
            cfg.ollama_url,
            cfg.ollama_model,
            auto_install=cfg.auto_install_ollama,
        )
        logger.debug("Checking local Ollama at %s", cfg.ollama_url)
        if ollama.health_check():
            if cfg.auto_install_ollama:
                OllamaInstaller.ensure_ollama_available(cfg.ollama_model)
<<<<<<< HEAD
            llm_impl = ollama
=======
            llm_infra = ollama
>>>>>>> pr-1954
        else:
            logger.debug("Ollama not reachable; attempting installation")
            if cfg.auto_install_ollama:
                OllamaInstaller.ensure_ollama_available(cfg.ollama_model)
                if not ollama.health_check():
                    logger.warning("Using stub LLM implementation")
<<<<<<< HEAD
                    llm_impl = _NullLLMInfrastructure()
                else:
                    llm_impl = ollama
            else:
                logger.warning("Using stub LLM implementation")
                llm_impl = _NullLLMInfrastructure()
=======
                    llm_infra = _NullLLMInfrastructure()
                else:
                    llm_infra = ollama
            else:
                logger.warning("Using stub LLM implementation")
                llm_infra = _NullLLMInfrastructure()
>>>>>>> pr-1954

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
<<<<<<< HEAD
    llm_resource = LLMResource(llm_impl)
=======
    llm_resource = LLMResource(llm_infra)
>>>>>>> pr-1954
    storage_resource = LocalStorageResource(storage_infra)

    return {
        "memory": Memory(db_resource, vector_resource),
        "llm": LLM(llm_resource),
        "storage": Storage(storage_resource),
        "logging": logging_resource,
    }
