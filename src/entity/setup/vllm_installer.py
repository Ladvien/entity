<<<<<<< HEAD
<<<<<<< HEAD
"""Utilities for validating local vLLM availability."""

from __future__ import annotations

import importlib
import logging


class VLLMInstaller:
    """Ensure the vLLM package is installed."""
=======
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
    """Install vLLM and download models for local execution."""

    DEFAULT_MODEL: Final[str] = "Qwen/Qwen2.5-0.5B-Instruct"
>>>>>>> pr-1946
=======
import logging
import importlib.util
import os
import subprocess
import sys


class VLLMInstaller:
    """Install the vLLM package when not already present."""
>>>>>>> pr-1954

    logger = logging.getLogger(__name__)

    @classmethod
<<<<<<< HEAD
<<<<<<< HEAD
    def ensure_vllm_available(cls) -> None:
        try:
            importlib.import_module("vllm")
            cls.logger.debug("vLLM package available")
        except ModuleNotFoundError:
            cls.logger.warning("vLLM package not installed")
=======
    def ensure_vllm_available(cls, model: str | None = None) -> None:
        """Install vLLM with the best backend and download ``model``."""

        model = model or cls.DEFAULT_MODEL
        auto_install_env = os.getenv("ENTITY_AUTO_INSTALL_VLLM", "true").lower()
        auto_install = auto_install_env in {"1", "true", "yes"}
        if not auto_install:
            cls.logger.debug("Auto install disabled via environment")
            return

        if not cls._vllm_installed():
            backend = cls._detect_backend()
            cls._install_vllm(backend)
        else:
            cls.logger.debug("vLLM package already installed")

        cls._download_model(model)

    # Helpers --------------------------------------------------------------
    @classmethod
    def _vllm_installed(cls) -> bool:
        return importlib.util.find_spec("vllm") is not None

    @classmethod
    def _detect_backend(cls) -> str:
        """Return cuda, rocm, metal, or cpu based on system capabilities."""

        try:
            import torch  # type: ignore

            if torch.cuda.is_available():
                return "cuda"
        except Exception:  # pragma: no cover - optional dependency
            pass

        if shutil.which("rocminfo"):
            return "rocm"

        if platform.system() == "Darwin":
            return "metal"

        return "cpu"

    @classmethod
    def _install_vllm(cls, backend: str) -> None:
        package_map = {
            "cuda": "vllm[cuda]",
            "rocm": "vllm[rocm]",
            "metal": "vllm[metal]",
            "cpu": "vllm",
        }
        package = package_map.get(backend, "vllm")
        cls.logger.info("Installing %s", package)
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    package,
                ],
                check=True,
            )
        except Exception as exc:  # pragma: no cover - installation errors
            cls.logger.error("Failed to install %s: %s", package, exc)

    @classmethod
    def _download_model(cls, model: str) -> None:
        cls.logger.info("Downloading model %s from HuggingFace", model)
        try:
            snapshot_download(
                repo_id=model, local_dir=None, local_dir_use_symlinks=True
            )
        except Exception as exc:  # pragma: no cover - network errors
            cls.logger.warning(
                "Unable to download model %s: %s. Configure HuggingFace CLI if necessary.",
                model,
                exc,
            )
>>>>>>> pr-1946
=======
    def ensure_vllm_available(cls, model: str | None = None) -> None:
        """Install vLLM via pip if ``ENTITY_AUTO_INSTALL_VLLM`` is truthy."""

        auto_env = os.getenv("ENTITY_AUTO_INSTALL_VLLM", "true").lower()
        if auto_env not in {"1", "true", "yes"}:
            cls.logger.debug("Auto install disabled via environment")
            return

        if importlib.util.find_spec("vllm") is None:
            cls.logger.info("Installing vLLM package")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "vllm"], check=False
            )
        else:
            cls.logger.debug("vLLM package already available")
>>>>>>> pr-1954
