from __future__ import annotations

"""High-level Agent wrapper with sensible defaults."""

import asyncio
import copy
from typing import Any, Dict

import yaml

from pipeline import SystemInitializer, SystemRegistries, execute_pipeline
from pipeline.defaults import DEFAULT_CONFIG, discover_local_ollama


class Agent:
    """Simple agent that executes the pipeline."""

    def __init__(
        self,
        config: Dict | str | None = None,
        *,
        llm: Dict | str | None = None,
        database: Dict | str | bool | None = None,
        logging: Dict | str | bool | None = None,
    ) -> None:
        base_cfg = self._load_config(config)
        if base_cfg is None:
            base_cfg = copy.deepcopy(DEFAULT_CONFIG)
        if any(arg is not None for arg in (llm, database, logging)):
            self._apply_kwargs(base_cfg, llm=llm, database=database, logging=logging)
        if "ollama" not in base_cfg.get("plugins", {}).get("resources", {}):
            detected = discover_local_ollama()
            if detected:
                base_cfg.setdefault("plugins", {}).setdefault("resources", {})[
                    "ollama"
                ] = detected
        self.config = base_cfg
        self.initializer = SystemInitializer(self.config)
        self._registries: SystemRegistries | None = None

    @staticmethod
    def _load_config(config: Dict | str | None) -> Dict | None:
        if isinstance(config, str):
            with open(config, "r") as fh:
                return yaml.safe_load(fh)
        return copy.deepcopy(config) if config is not None else None

    @staticmethod
    def _normalize(value: Dict | str | bool | None) -> Dict | None:
        if value is False or value is None:
            return None
        if isinstance(value, str):
            return {"type": value}
        if isinstance(value, dict):
            return value
        raise TypeError(f"Unsupported config type: {type(value)!r}")

    def _apply_kwargs(
        self,
        config: Dict,
        *,
        llm: Dict | str | None = None,
        database: Dict | str | bool | None = None,
        logging: Dict | str | bool | None = None,
    ) -> None:
        resources = config.setdefault("plugins", {}).setdefault("resources", {})
        mapping = {"ollama": llm, "database": database, "logging": logging}
        for name, value in mapping.items():
            if value is not None:
                normalized = self._normalize(value)
                if normalized is None:
                    resources.pop(name, None)
                else:
                    resources[name] = normalized

    async def _ensure_initialized(self) -> None:
        if self._registries is None:
            initialized = await self.initializer.initialize()
            if isinstance(initialized, tuple):
                plugin_reg, resource_reg, tool_reg = initialized
                self._registries = SystemRegistries(
                    resources=resource_reg,
                    tools=tool_reg,
                    plugins=plugin_reg,
                )
            else:
                self._registries = initialized

    async def handle(self, message: str) -> Any:
        await self._ensure_initialized()
        if self._registries is None:
            raise RuntimeError("System not initialized")
        return await execute_pipeline(message, self._registries)

    # Convenience synchronous API
    def run_http(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        asyncio.run(self.serve_http(host, port))

    async def serve_http(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        from pipeline.adapters.http import HTTPAdapter

        await self._ensure_initialized()
        if self._registries is None:
            raise RuntimeError("System not initialized")
        adapter = HTTPAdapter({"host": host, "port": port})
        await adapter.serve(self._registries)
