"""Utilities for ensuring vLLM is installed with the correct backend."""

from __future__ import annotations

import importlib.util
import sys
import logging
import os
import platform
import shutil
import subprocess
from typing import Final

from huggingface_hub import snapshot_download


class VLLMInstaller:
    """Placeholder for vLLM installation logic.
    Automatic installation and model downloading are not supported by the framework.
    """

    DEFAULT_MODEL: Final[str] = "Qwen/Qwen2.5-0.5B-Instruct"

    logger = logging.getLogger(__name__)

    @classmethod
    def ensure_vllm_available(cls, model: str | None = None) -> None:
        cls.logger.warning("Automatic vLLM installation and model downloading are not supported by the framework.")
        cls.logger.warning("Please ensure vLLM is installed and the model is available manually.")
        
