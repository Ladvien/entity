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




class OllamaInstaller:
    """Placeholder for Ollama installation logic.
    Automatic installation and model pulling are not supported by the framework.
    """

    DEFAULT_MODEL: Final[str] = "llama3.2:3b"
    DEFAULT_URL: Final[str] = "http://localhost:11434"

    logger = logging.getLogger(__name__)

    @classmethod
    def ensure_ollama_available(cls, model: str | None = None) -> None:
        cls.logger.warning("Automatic Ollama installation and model pulling are not supported by the framework.")
        cls.logger.warning("Please ensure Ollama is installed and the model is available manually.")

