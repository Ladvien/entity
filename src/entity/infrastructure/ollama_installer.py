import logging
import subprocess


class OllamaInstaller:
    """Attempt to install the Ollama server locally."""

    @classmethod
    def ensure_installed(cls) -> None:
        logger = logging.getLogger(cls.__name__)
        try:
            subprocess.run(
                ["ollama", "--version"],
                check=True,
                capture_output=True,
                timeout=5,
            )
            logger.debug("Ollama already installed")
            return
        except Exception as exc:
            logger.debug("Ollama not found: %s", exc)

        logger.info("Attempting automatic Ollama installation")
        try:
            subprocess.run(
                "curl -fsSL https://ollama.com/install.sh | sh",
                shell=True,
                check=True,
                timeout=5,
                capture_output=True,
            )
            logger.info("Ollama installation complete")
        except Exception as exc:
            logger.warning("Automatic installation failed: %s", exc)
