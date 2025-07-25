import logging
import platform
import shutil
import subprocess


class OllamaInstaller:
    """Utility class for installing Ollama and managing models."""

    logger = logging.getLogger(__name__)

    @classmethod
    def ensure_installed(cls) -> None:
        """Install Ollama if it is not already present."""

        if shutil.which("ollama"):
            cls.logger.debug("Ollama binary found")
            return

        system = platform.system()
        try:
            if system == "Darwin":
                cls.logger.debug("Installing Ollama via Homebrew")
                subprocess.run(["brew", "install", "ollama"], check=True)
            elif system == "Linux":
                cls.logger.debug("Installing Ollama via install script")
                subprocess.run(
                    ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
                    check=True,
                )
            elif system == "Windows":
                cls.logger.debug("Installing Ollama via winget")
                subprocess.run(
                    [
                        "winget",
                        "install",
                        "-e",
                        "--id",
                        "Ollama.Ollama",
                    ],
                    check=True,
                )
            else:
                cls.logger.warning("Unsupported platform: %s", system)
        except PermissionError as exc:
            cls.logger.warning("Permission denied while installing Ollama: %s", exc)
        except subprocess.CalledProcessError as exc:
            cls.logger.error("Failed to install Ollama: %s", exc)

    @classmethod
    def pull_default_model(cls, model: str) -> None:
        """Download the specified model using ``ollama pull``."""

        if not shutil.which("ollama"):
            cls.logger.debug("Ollama not installed; skipping model pull")
            return

        try:
            cls.logger.debug("Pulling model %s", model)
            subprocess.run(["ollama", "pull", model], check=True)
        except PermissionError as exc:
            cls.logger.warning("Permission denied while pulling model: %s", exc)
        except subprocess.CalledProcessError as exc:
            cls.logger.error("Failed to pull model %s: %s", model, exc)
