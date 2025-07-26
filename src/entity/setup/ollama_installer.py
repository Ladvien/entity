"""Utilities for automatically setting up the Ollama service."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import time
from typing import Final

import httpx

# TODO: Expose installation paths and URLs via configuration


class OllamaInstaller:
    """Handle installation and startup of the local Ollama service."""

    DEFAULT_MODEL: Final[str] = "llama3.2:3b"
    DEFAULT_URL: Final[str] = "http://localhost:11434"

    logger = logging.getLogger(__name__)

    @classmethod
    def ensure_ollama_available(cls, model: str | None = None) -> None:
        """Install and start Ollama if required."""

        model = model or cls.DEFAULT_MODEL
        auto_install_env = os.getenv("ENTITY_AUTO_INSTALL_OLLAMA", "true").lower()
        auto_install = auto_install_env in {"1", "true", "yes"}

        if not auto_install:
            cls.logger.debug("Auto install disabled via environment")
            return

        if not shutil.which("ollama"):
            cls.logger.info("Ollama binary not found; attempting install")
            cls._install_ollama()
        else:
            cls.logger.debug("Ollama binary already present")

        if not cls._service_healthy():
            cls.logger.info("Starting local Ollama service")
            cls._start_service()
            if not cls._wait_for_service():
                cls.logger.warning("Ollama service failed to start")
                return

        cls._pull_model(model)

    # Installation helpers -------------------------------------------------
    @classmethod
    def _install_ollama(cls) -> None:
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(["brew", "install", "ollama"], check=True)
            elif system == "Linux":
                subprocess.run(
                    ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
                    check=True,
                )
            elif system == "Windows":
                subprocess.run(
                    ["winget", "install", "-e", "--id", "Ollama.Ollama"],
                    check=True,
                )
            else:
                cls.logger.warning("Unsupported platform: %s", system)
        except subprocess.CalledProcessError as exc:
            cls.logger.error("Failed to install Ollama: %s", exc)

    # Service management ---------------------------------------------------
    @classmethod
    def _start_service(cls) -> None:
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(0.5)  # Give subprocess a moment
            # TODO: Consider platform specific service managers
        except Exception as exc:  # pragma: no cover - rare
            cls.logger.error("Unable to start Ollama service: %s", exc)

    @classmethod
    def _service_healthy(cls) -> bool:
        try:
            httpx.get(f"{cls.DEFAULT_URL}/api/tags", timeout=1).raise_for_status()
            return True
        except Exception:
            return False

    @classmethod
    def _wait_for_service(cls, retries: int = 5, delay: float = 1.0) -> bool:
        for _ in range(retries):
            if cls._service_healthy():
                return True
            time.sleep(delay)
        return False

    # Model helpers --------------------------------------------------------
    @classmethod
    def _pull_model(cls, model: str) -> None:
        try:
            result = subprocess.run(
                ["ollama", "pull", model],
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stderr:
                cls.logger.debug("ollama pull stderr: %s", result.stderr)
        except subprocess.CalledProcessError as exc:
            err_text = (exc.stderr or str(exc)).lower()
            if "id_ed25519" in err_text or "no such file" in err_text:
                cls.logger.error(
                    "Ollama key not found. Run 'ollama login' to generate ~/.ollama/id_ed25519."
                )
                raise RuntimeError(
                    "Missing Ollama key. Run 'ollama login' and try again."
                ) from exc

            cls.logger.error("Failed to pull model %s: %s", model, exc)
            raise
