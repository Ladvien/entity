"""Utilities for validating local vLLM availability."""

from __future__ import annotations

import importlib
import logging


class VLLMInstaller:
    """Ensure the vLLM package is installed."""

    logger = logging.getLogger(__name__)

    @classmethod
    def ensure_vllm_available(cls) -> None:
        try:
            importlib.import_module("vllm")
            cls.logger.debug("vLLM package available")
        except ModuleNotFoundError:
            cls.logger.warning("vLLM package not installed")
