from __future__ import annotations

import asyncio
from typing import Dict, Sequence

import httpx

from entity.core.plugins import InfrastructurePlugin, ValidationResult


class LlamaCppInfrastructure(InfrastructurePlugin):
    """Launch a local llama.cpp server."""

    name = "llamacpp"
    infrastructure_type = "llm_provider"
    resource_category = "infrastructure"
    stages: list = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.binary = self.config.get("binary", "llama")
        self.model = self.config.get("model", "")
        self.host = self.config.get("host", "127.0.0.1")
        self.port = int(self.config.get("port", 8000))
        self.args: Sequence[str] = self.config.get("args", [])
        self._process: asyncio.subprocess.Process | None = None

    async def initialize(self) -> None:
        if self._process is not None:
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
        self._process = await asyncio.create_subprocess_exec(*cmd)

    async def validate_runtime(self) -> ValidationResult:
        url = f"http://{self.host}:{self.port}/health"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=5.0)
                resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    async def shutdown(self) -> None:
        if self._process is None:
            return
        self._process.terminate()
        try:
            await asyncio.wait_for(self._process.wait(), timeout=5)
        except Exception:  # noqa: BLE001 - best effort cleanup
            self._process.kill()
        self._process = None
