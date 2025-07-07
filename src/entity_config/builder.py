from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

from pipeline.config import ConfigLoader

from .validators import _validate_memory, _validate_vector_memory


@dataclass
class ConfigBuilder:
    """Programmatic builder for Entity configuration."""

    config: Dict[str, Any] = field(
        default_factory=lambda: {
            "server": {
                "host": "127.0.0.1",
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

    def validate(self) -> None:
        _validate_memory(self.config)
        _validate_vector_memory(self.config)

    def build(self) -> Dict[str, Any]:
        self.validate()
        return ConfigLoader.from_dict(self.config, self.env_file)


__all__ = ["ConfigBuilder"]
