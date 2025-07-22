"""Entity agent framework package."""

from importlib.metadata import version as _version

try:
    __version__ = _version("entity")
except Exception:  # pragma: no cover - package not installed
    __version__ = "0.0.0"

from .core.agent import Agent

__all__ = ["Agent", "__version__"]
