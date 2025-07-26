import logging
import importlib.util
import os
import subprocess
import sys


class VLLMInstaller:
    """Install the vLLM package when not already present."""

    logger = logging.getLogger(__name__)

    @classmethod
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
