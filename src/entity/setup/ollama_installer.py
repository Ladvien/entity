"""Utilities for automatically setting up the Ollama service."""

from __future__ import annotations

import logging
from typing import Final


class OllamaInstaller:
    """Placeholder for Ollama installation logic.
    Automatic installation and model pulling are not supported by the framework.
    """

    DEFAULT_MODEL: Final[str] = "llama3.2:3b"
    DEFAULT_URL: Final[str] = "http://localhost:11434"

    logger = logging.getLogger(__name__)

    @classmethod
    def ensure_ollama_available(cls, model: str | None = None) -> None:
        cls.logger.debug("Checking Ollama availability...")
