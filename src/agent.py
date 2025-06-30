from __future__ import annotations

import asyncio
import copy
from typing import Any

import yaml

from pipeline import SystemInitializer, SystemRegistries, execute_pipeline
from pipeline.adapters import HTTPAdapter


class Agent:
    """Simple agent wrapper that can run an HTTP server."""

    def __init__(
        self,
        config: dict | str | None = None,
        *,
        llm: dict | str | None = None,
        database: dict | str | bool | None = None,
        logging: dict | str | bool | None = None,
    ) -> None:
        if isinstance(config, str):
            with open(config, "r") as fh:
                base_config = yaml.safe_load(fh)
        else:
            base_config = copy.deepcopy(config) if config is not None else None

        if any(arg is not None for arg in (llm, database, logging)):
            base_config = (
                copy.deepcopy(base_config)
                if base_config
                else copy.deepcopy(SystemInitializer.DEFAULT_CONFIG)
            )

            resources = base_config.setdefault("plugins", {}).setdefault(
                "resources", {}
            )

            def normalize(value: dict | str | bool | None) -> dict | None:
                if value is False or value is None:
                    return None
                if isinstance(value, str):
                    return {"type": value}
                if isinstance(value, dict):
                    return value
                raise TypeError(f"Unsupported config type: {type(value)!r}")

            mapping = {
                "llm": ("ollama", llm),
                "database": ("database", database),
                "logging": ("logging", logging),
            }

            for name, value in mapping.values():
                if value is not None:
                    cfg = normalize(value)
                    if cfg is None:
                        resources.pop(name, None)
                    else:
                        resources[name] = cfg

            self.config = base_config
        else:
            self.config = base_config

        self.initializer = SystemInitializer(self.config)
        self._registries: SystemRegistries | None = None

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

    def run(self) -> None:
        async def _run() -> None:
            await self._ensure_initialized()
            if self._registries is None:
                raise RuntimeError("System not initialized")
            server_cfg = (self.config or {}).get("server", {})
            adapter = HTTPAdapter(server_cfg)
            await adapter.serve(self._registries)

        asyncio.run(_run())
