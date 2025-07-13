from __future__ import annotations

import asyncio
from typing import Dict, List

import httpx

from entity.core.plugins import InfrastructurePlugin


class LlamaCppInfrastructure(InfrastructurePlugin):
    """Run a local llama.cpp server."""

    name = "llamacpp"
    infrastructure_type = "llm_provider"
    stages: List = []
    dependencies: List[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.binary = self.config.get("binary", "llama")
        self.model = self.config.get("model")
        self.host = self.config.get("host", "127.0.0.1")
        self.port = int(self.config.get("port", 8000))
        self.args = self.config.get("args", [])
        self._proc: asyncio.subprocess.Process | None = None

    async def initialize(self) -> None:
        if self._proc is not None:
            return
        cmd = [
            self.binary,
            "--model",
            self.model,
            "--host",
            self.host,
            "--port",
            str(self.port),
            *self.args,
        ]
        self._proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def validate_runtime(self) -> bool:
        url = f"http://{self.host}:{self.port}/health"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
            return resp.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    async def shutdown(self) -> None:
        if self._proc is None:
            return
        self._proc.terminate()
        try:
            await asyncio.wait_for(self._proc.wait(), timeout=5)
        except asyncio.TimeoutError:  # pragma: no cover - best effort cleanup
            self._proc.kill()
        self._proc = None
