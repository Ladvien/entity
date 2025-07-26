from __future__ import annotations

import asyncio
import socket
import subprocess
import sys
import time
from typing import Final

import httpx

from .base import BaseInfrastructure
from entity.setup.vllm_installer import VLLMInstaller


class VLLMInfrastructure(BaseInfrastructure):
    """Layer 1 infrastructure for running a local vLLM service."""

    MODEL_SELECTION_MATRIX: Final[dict[str, dict[str, list[str] | str]]] = {
        "high_gpu": {
            "models": ["meta-llama/Llama-3.1-8b-instruct", "Qwen/Qwen2.5-7B-Instruct"],
            "priority": "performance",
        },
        "medium_gpu": {
            "models": ["Qwen/Qwen2.5-3B-Instruct", "microsoft/DialoGPT-medium"],
            "priority": "balanced",
        },
        "low_gpu": {
            "models": [
                "Qwen/Qwen2.5-1.5B-Instruct",
                "Qwen/Qwen2.5-0.5B-Instruct",
            ],
            "priority": "efficiency",
        },
        "cpu_only": {
            "models": ["Qwen/Qwen2.5-0.5B-Instruct"],
            "priority": "compatibility",
        },
    }

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        *,
        auto_detect_model: bool = True,
        gpu_memory_utilization: float = 0.9,
        port: int | None = None,
        version: str | None = None,
        auto_install: bool = True,
    ) -> None:
        super().__init__(version)
        self.model = (
            model
            if model is not None or not auto_detect_model
            else self._detect_optimal_model()
        )
        self.gpu_memory_utilization = gpu_memory_utilization
        self.port = port or self._find_available_port()
        self.base_url = (
            base_url.rstrip("/") if base_url else f"http://localhost:{self.port}"
        )
        self.auto_install = auto_install
        self._server_process: subprocess.Popen | None = None

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate",
                json={"prompt": prompt, "model": self.model},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("text", "")

    def health_check(self) -> bool:
        for attempt in range(3):
            try:
                resp = httpx.get(f"{self.base_url}/health", timeout=2)
                resp.raise_for_status()
                self.logger.debug(
                    "Health check succeeded for %s on attempt %s",
                    self.base_url,
                    attempt + 1,
                )
                return True
            except Exception as exc:
                self.logger.debug(
                    "Health check attempt %s failed for %s: %s",
                    attempt + 1,
                    self.base_url,
                    exc,
                )
                time.sleep(1)

        self.logger.warning("Health check failed for %s", self.base_url)
        if self.auto_install:
            self.logger.debug("Attempting automatic vLLM install")
            VLLMInstaller.ensure_vllm_available(self.model)
        return False

    # ------------------------------------------------------------------
    @staticmethod
    def _detect_hardware_tier() -> str:
        """Return a hardware tier string based on available GPU memory."""
        memory_gb = None
        try:  # Prefer torch if installed
            import torch  # type: ignore

            if torch.cuda.is_available():
                memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except Exception:  # pragma: no cover - torch optional
            memory_gb = None

        if memory_gb is None:
            try:
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=memory.total",
                        "--format=csv,noheader",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                memory_mb = int(result.stdout.splitlines()[0].split()[0])
                memory_gb = memory_mb / 1024
            except Exception:  # pragma: no cover - command may not exist
                memory_gb = None

        if memory_gb is None:
            return "cpu_only"
        if memory_gb > 16:
            return "high_gpu"
        if memory_gb >= 4:
            return "medium_gpu"
        return "low_gpu"

    def _detect_optimal_model(self) -> str:
        tier = self._detect_hardware_tier()
        return self.MODEL_SELECTION_MATRIX[tier]["models"][0]

    @staticmethod
    def _find_available_port() -> int:
        with socket.socket() as sock:
            sock.bind(("localhost", 0))
            return sock.getsockname()[1]

    async def startup(self) -> None:  # pragma: no cover - thin wrapper
        await super().startup()
        if not self._server_process:
            await self._start_vllm_server()

    async def shutdown(self) -> None:  # pragma: no cover - thin wrapper
        await super().shutdown()
        if self._server_process and self._server_process.poll() is None:
            self._server_process.terminate()
            try:
                self._server_process.wait(timeout=10)
            except Exception:
                self._server_process.kill()
        self._server_process = None

    async def _start_vllm_server(self) -> None:
        """Launch the vLLM API server as a subprocess."""
        cmd = [
            sys.executable,
            "-m",
            "vllm.entrypoints.api_server",
            "--model",
            self.model,
            "--port",
            str(self.port),
            "--gpu-memory-utilization",
            str(self.gpu_memory_utilization),
        ]
        self.logger.info("Starting vLLM server: %s", " ".join(cmd))
        self._server_process = subprocess.Popen(cmd)

        # Wait for the server to become responsive
        for _ in range(20):
            if self.health_check():
                return
            await asyncio.sleep(0.5)
        raise RuntimeError("vLLM server failed to start")
