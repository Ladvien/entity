from __future__ import annotations

import asyncio

import yaml

from pipeline import SystemInitializer, execute_pipeline
from pipeline.adapters.http import HttpAdapter


class Agent:
    """Simple agent wrapper that can run an HTTP server."""

    def __init__(self, config: dict | str | None = None) -> None:
        if isinstance(config, str):
            with open(config, "r") as fh:
                self.config = yaml.safe_load(fh)
        else:
            self.config = config or {}
        self.initializer = SystemInitializer(self.config)
        self._registries = None

    async def _ensure_initialized(self) -> None:
        if self._registries is None:
            self._registries = await self.initializer.initialize()

    async def handle(self, message: str):
        await self._ensure_initialized()
        return await execute_pipeline(message, self._registries)

    def run(self) -> None:
        async def _run() -> None:
            await self._ensure_initialized()
            server_cfg = self.config.get("server", {})
            adapter = HttpAdapter(server_cfg)
            await adapter.serve(self._registries)

        asyncio.run(_run())
