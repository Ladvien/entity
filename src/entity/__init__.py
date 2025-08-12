"""Entity agent framework package."""

from importlib.metadata import version as _version

try:
    __version__ = _version("entity")
except Exception:
    __version__ = "0.0.0"

__all__ = ["Agent", "__version__"]


def __getattr__(name: str):
    if name == "Agent":
        from entity.core.agent import Agent

        return Agent
    raise AttributeError(name)
