import warnings
from importlib import import_module

warnings.warn(
    "The 'pipeline' package is deprecated. Use 'entity.pipeline' instead.",
    DeprecationWarning,
    stacklevel=2,
)

_module = import_module("entity.pipeline")

__all__ = getattr(_module, "__all__", [])


def __getattr__(name: str):
    return getattr(_module, name)
