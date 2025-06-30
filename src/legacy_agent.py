from __future__ import annotations

import asyncio
import copy
from typing import Any

import yaml

from pipeline import SystemInitializer, SystemRegistries, execute_pipeline


class Agent:
    """Simple agent that executes the pipeline."""

    def __init__(
        self,
        config: dict | str | None = None,
        *,
        llm: dict | str | None = None,
        database: dict | str | bool | None = None,
        logging: dict | str | bool | None = None,
    ) -> None:
        base_cfg = self._load_config(config)
        if any(arg is not None for arg in (llm, database, logging)):
            base_cfg = base_cfg or copy.deepcopy(SystemInitializer.DEFAULT_CONFIG)
            self._apply_kwargs(base_cfg, llm=llm, database=database, logging=logging)
        self.config = base_cfg

        self.initializer = SystemInitializer(self.config)
        self._registries: SystemRegistries | None = None

    @staticmethod
    def _load_config(config: dict | str | None) -> dict | None:
        if isinstance(config, str):
            with open(config, "r") as fh:
                return yaml.safe_load(fh)
        return copy.deepcopy(config) if config is not None else None

    @staticmethod
    def _normalize(value: dict | str | bool | None) -> dict | None:
        if value is False or value is None:
            return None
        if isinstance(value, str):
            return {"type": value}
        if isinstance(value, dict):
            return value
        raise TypeError(f"Unsupported config type: {type(value)!r}")

    def _apply_kwargs(
        self,
        config: dict,
        *,
        llm: dict | str | None = None,
        database: dict | str | bool | None = None,
        logging: dict | str | bool | None = None,
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
