from __future__ import annotations

<<<<<<< HEAD
<<<<<<< HEAD
import asyncio
import socket
import subprocess
import time
from typing import Any

=======
>>>>>>> pr-1950
=======
>>>>>>> pr-1947
import httpx

from .base import BaseInfrastructure


class VLLMInfrastructure(BaseInfrastructure):
<<<<<<< HEAD
<<<<<<< HEAD
    """Layer 1 infrastructure for vLLM serving with automatic resource detection."""

    MODEL_SELECTION_MATRIX = {
        "high_gpu": {
            "models": [
                "meta-llama/Llama-3.1-8b-instruct",
                "Qwen/Qwen2.5-7B-Instruct",
            ],
            "priority": "performance",
        },
        "medium_gpu": {
            "models": ["Qwen/Qwen2.5-3B-Instruct", "microsoft/DialoGPT-medium"],
            "priority": "balanced",
        },
        "low_gpu": {
            "models": ["Qwen/Qwen2.5-1.5B-Instruct", "Qwen/Qwen2.5-0.5B-Instruct"],
            "priority": "efficiency",
        },
        "cpu_only": {
            "models": ["Qwen/Qwen2.5-0.5B-Instruct"],
            "priority": "compatibility",
        },
    }

    def __init__(
        self,
        model: str | None = None,
        auto_detect_model: bool = True,
        gpu_memory_utilization: float = 0.9,
        port: int | None = None,
        version: str | None = None,
    ) -> None:
        super().__init__(version)
        self.model = model or (
            self._detect_optimal_model()
            if auto_detect_model
            else "Qwen/Qwen2.5-0.5B-Instruct"
        )
        self.gpu_memory_utilization = gpu_memory_utilization
        self.port = port or self._find_available_port()
        self._server_process: subprocess.Popen | None = None

    def _find_available_port(self) -> int:
        with socket.socket() as s:
            s.bind(("localhost", 0))
            return s.getsockname()[1]

    def _detect_hardware_tier(self) -> str:
        try:
            import torch  # type: ignore

            if torch.cuda.is_available():
                mem_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
                if mem_gb > 16:
                    return "high_gpu"
                if mem_gb >= 4:
                    return "medium_gpu"
                return "low_gpu"
        except Exception as exc:  # pragma: no cover - optional dependency
            self.logger.debug("GPU detection failed: %s", exc)
        return "cpu_only"

    def _detect_optimal_model(self) -> str:
        hardware_tier = self._detect_hardware_tier()
        return self.MODEL_SELECTION_MATRIX[hardware_tier]["models"][0]

    async def startup(self) -> None:
        await super().startup()
        if not self._server_process:
            await self._start_vllm_server()

    async def shutdown(self) -> None:
        await super().shutdown()
        if self._server_process and self._server_process.poll() is None:
            self._server_process.terminate()
            try:
                self._server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:  # pragma: no cover - unlikely
                self._server_process.kill()
        self._server_process = None

    def health_check(self) -> bool:
        if self._server_process and self._server_process.poll() is not None:
            return False
        try:
            response = httpx.get(f"http://localhost:{self.port}/health", timeout=2)
            return response.status_code == 200
        except Exception as exc:  # pragma: no cover - network errors
            self.logger.debug("Health check failed: %s", exc)
            return False

    async def _start_vllm_server(self) -> None:
        cmd = [
            "python",
            "-m",
            "vllm.entrypoints.openai.api_server",
            "--model",
            self.model,
            "--port",
            str(self.port),
            "--gpu-memory-utilization",
            str(self.gpu_memory_utilization),
        ]
        self.logger.debug("Starting vLLM server: %s", " ".join(cmd))
        self._server_process = subprocess.Popen(cmd)
        await asyncio.sleep(1)
=======
    """Simple infrastructure wrapper for a vLLM server."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        model: str | None = None,
        version: str | None = None,
    ) -> None:
=======
    """Layer 1 infrastructure for a vLLM server."""

    def __init__(self, base_url: str, model: str, version: str | None = None) -> None:
>>>>>>> pr-1947
        super().__init__(version)
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/generate",
<<<<<<< HEAD
                json={"prompt": prompt, "model": self.model},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    def health_check(self) -> bool:
        try:
            httpx.get(f"{self.base_url}/health", timeout=1).raise_for_status()
            return True
        except Exception as exc:  # pragma: no cover - network errors
            self.logger.debug("vLLM health check failed: %s", exc)
            return False
>>>>>>> pr-1950
=======
                json={"model": self.model, "prompt": prompt},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", data.get("text", ""))

    def health_check(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=2)
            response.raise_for_status()
            return True
        except Exception:
            return False
>>>>>>> pr-1947
