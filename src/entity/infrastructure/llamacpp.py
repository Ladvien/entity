from __future__ import annotations

import asyncio
<<<<<<< HEAD
from typing import Dict, List

import httpx

from entity.core.plugins import InfrastructurePlugin


class LlamaCppInfrastructure(InfrastructurePlugin):
    """Run a local llama.cpp server."""

    name = "llamacpp"
    infrastructure_type = "llm_provider"
    stages: List = []
    dependencies: List[str] = []
=======
from typing import Dict, Sequence

import httpx

from entity.core.plugins import InfrastructurePlugin, ValidationResult


class LlamaCppInfrastructure(InfrastructurePlugin):
    """Launch a local llama.cpp server."""

    name = "llamacpp"
    infrastructure_type = "llm_provider"
    resource_category = "infrastructure"
    stages: list = []
    dependencies: list[str] = []
>>>>>>> pr-1480

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.binary = self.config.get("binary", "llama")
<<<<<<< HEAD
        self.model = self.config.get("model")
        self.host = self.config.get("host", "127.0.0.1")
        self.port = int(self.config.get("port", 8000))
        self.args = self.config.get("args", [])
        self._proc: asyncio.subprocess.Process | None = None

    async def initialize(self) -> None:
        if self._proc is not None:
=======
        self.model = self.config.get("model", "")
        self.host = self.config.get("host", "127.0.0.1")
        self.port = int(self.config.get("port", 8000))
        self.args: Sequence[str] = self.config.get("args", [])
        self._process: asyncio.subprocess.Process | None = None

    async def initialize(self) -> None:
        if self._process is not None:
>>>>>>> pr-1480
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
<<<<<<< HEAD
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
=======
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
>>>>>>> pr-1480
