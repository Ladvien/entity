from __future__ import annotations

import asyncio
from typing import Any

import yaml

from pipeline import SystemInitializer, SystemRegistries, execute_pipeline
from pipeline.adapters import HTTPAdapter


class Agent:
    """Simple agent wrapper that can run an HTTP server."""

    def __init__(self, config: dict | str | None = None) -> None:
        if isinstance(config, str):
            with open(config, "r") as fh:
                self.config = yaml.safe_load(fh)
        else:
            self.config = config
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
