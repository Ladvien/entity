from __future__ import annotations

import asyncio

from .utils.logging import get_logger
from .utils.setup_manager import Layer0SetupManager

logger = get_logger(__name__)

_setup: Layer0SetupManager | None = None


def ensure_defaults(**kwargs) -> Layer0SetupManager:
    """Prepare local resources using :class:`Layer0SetupManager`."""
    global _setup
    if _setup is None:
        _setup = Layer0SetupManager(**kwargs)
        try:
            asyncio.run(_setup.setup())
        except Exception:  # noqa: BLE001 - best effort
            logger.debug("Default setup failed", exc_info=True)
    return _setup


def ollama_available(
    model: str = "llama3", base_url: str = "http://localhost:11434"
) -> bool:
    """Return ``True`` if Ollama is reachable and the model is present."""
    manager = Layer0SetupManager(model=model, base_url=base_url)
    try:
        return asyncio.run(manager.ensure_ollama())
    except Exception:  # noqa: BLE001 - optional runtime dependency
        logger.debug("Ollama check failed", exc_info=True)
        return False


def _reset_defaults() -> None:  # pragma: no cover - testing helper
    global _setup
    _setup = None
