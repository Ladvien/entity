from __future__ import annotations

"""Experimental encrypted config loader."""

import os
from pathlib import Path
from typing import Any, Protocol

import yaml
from cryptography.fernet import Fernet

from pipeline.config import ConfigLoader


class SecretsProvider(Protocol):
    """Protocol for retrieving secrets."""

    def get_secret(self, name: str) -> str: ...


class EnvSecretsProvider:
    """Secrets provider that reads from environment variables."""

    def get_secret(self, name: str) -> str:
        value = os.getenv(name)
        if value is None:
            raise KeyError(f"Secret {name} not found in environment")
        return value


def sanitize_config(config: dict[str, Any]) -> dict[str, Any]:
    """Simple sanitization for server settings."""

    server = config.get("server", {})
    allowed_keys = {"host", "port", "reload", "log_level"}
    sanitized_server: dict[str, Any] = {
        key: server[key] for key in allowed_keys if key in server
    }
    port = sanitized_server.get("port")
    if port is not None:
        try:
            port_int = int(port)
            if not 1 <= port_int <= 65535:
                raise ValueError
        except (TypeError, ValueError) as exc:  # pragma: no cover - validation
            raise ValueError("server.port must be between 1 and 65535") from exc
        sanitized_server["port"] = port_int
    if sanitized_server:
        config["server"] = sanitized_server
    return config


class SecureConfigLoader:
    """Load and decrypt configuration files."""

    def __init__(
        self, provider: SecretsProvider, secret_name: str = "CONFIG_KEY"
    ) -> None:
        self.provider = provider
        self.secret_name = secret_name

    def _decrypt_file(self, path: Path) -> bytes:
        key = self.provider.get_secret(self.secret_name).encode()
        fernet = Fernet(key)
        encrypted = path.read_bytes()
        try:
            decrypted = fernet.decrypt(encrypted)
        except Exception as exc:  # pragma: no cover - error path
            raise ValueError(f"Failed to decrypt {path}") from exc
        return decrypted

    def load(self, path: str | Path, env_file: str = ".env") -> dict[str, Any]:
        """Return decrypted and validated configuration."""

        data = self._decrypt_file(Path(path))
        raw = yaml.safe_load(data) or {}
        raw = sanitize_config(raw)
        return ConfigLoader.from_dict(raw, env_file)
