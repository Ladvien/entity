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

    logger = logging.getLogger(__name__)

    @classmethod
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
