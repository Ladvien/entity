from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from pipeline.config import ConfigLoader


@dataclass
class ConfigBuilder:
    """Programmatic builder for Entity configuration."""

    config: Dict[str, Any] = field(
        default_factory=lambda: {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "reload": False,
                "log_level": "info",
            },
            "plugins": {
                "resources": {},
                "tools": {},
                "adapters": {},
                "prompts": {},
            },
        }
    )
    env_file: str = ".env"

    # ------------------------------------------------------------------
    # Section: Factory Methods
    # ------------------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str | Path, env_file: str = ".env") -> "ConfigBuilder":
        cfg = ConfigLoader.from_yaml(path, env_file)
        return cls(cfg, env_file)

    @classmethod
    def dev_preset(cls) -> "ConfigBuilder":
        path = Path(__file__).resolve().parents[2] / "config" / "dev.yaml"
        return cls.from_yaml(path)

    @classmethod
    def prod_preset(cls) -> "ConfigBuilder":
        path = Path(__file__).resolve().parents[2] / "config" / "prod.yaml"
        return cls.from_yaml(path)

    # ------------------------------------------------------------------
    # Section: Builder Methods
    # ------------------------------------------------------------------
    def set_server(
        self, host: str, port: int, reload: bool = False, log_level: str = "info"
    ) -> "ConfigBuilder":
        self.config["server"] = {
            "host": host,
            "port": port,
            "reload": reload,
            "log_level": log_level,
        }
        return self

    def add_resource(
        self, name: str, type_path: str, **options: Any
    ) -> "ConfigBuilder":
        self.config["plugins"]["resources"][name] = {"type": type_path, **options}
        return self

    def add_tool(self, name: str, type_path: str, **options: Any) -> "ConfigBuilder":
        self.config["plugins"]["tools"][name] = {"type": type_path, **options}
        return self

    def add_adapter(self, name: str, type_path: str, **options: Any) -> "ConfigBuilder":
        self.config["plugins"]["adapters"][name] = {"type": type_path, **options}
        return self

    def add_prompt(self, name: str, type_path: str, **options: Any) -> "ConfigBuilder":
        self.config["plugins"]["prompts"][name] = {"type": type_path, **options}
        return self

    # ------------------------------------------------------------------
    # Section: Validation
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_memory(cfg: dict) -> None:
        mem_cfg = cfg.get("plugins", {}).get("resources", {}).get("memory")
        if not mem_cfg:
            return
        backend = mem_cfg.get("backend")
        if backend is not None and not isinstance(backend, dict):
            raise ValueError("memory: 'backend' must be a mapping")
        if isinstance(backend, dict) and "type" in backend:
            if not isinstance(backend["type"], str):
                raise ValueError("memory: 'backend.type' must be a string")

    @staticmethod
    def _validate_vector_memory(cfg: dict) -> None:
        vm_cfg = cfg.get("plugins", {}).get("resources", {}).get("vector_memory")
        if not vm_cfg:
            return
        table = vm_cfg.get("table")
        if not isinstance(table, str) or not table:
            raise ValueError("vector_memory: 'table' is required")
        embedding = vm_cfg.get("embedding_model")
        if not isinstance(embedding, dict):
            raise ValueError("vector_memory: 'embedding_model' must be a mapping")
        if not embedding.get("name"):
            raise ValueError("vector_memory: 'embedding_model.name' is required")
        if "dimensions" in embedding:
            try:
                int(embedding["dimensions"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "vector_memory: 'embedding_model.dimensions' must be an integer"
                ) from exc

    def validate(self) -> None:
        self._validate_memory(self.config)
        self._validate_vector_memory(self.config)

    def build(self) -> Dict[str, Any]:
        self.validate()
        return ConfigLoader.from_dict(self.config, self.env_file)


__all__ = ["ConfigBuilder"]
