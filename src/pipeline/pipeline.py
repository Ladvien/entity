import warnings
from importlib import import_module

warnings.warn(
    "The 'pipeline.pipeline' module is deprecated. Use 'entity.pipeline.pipeline' instead.",
    DeprecationWarning,
    stacklevel=2,
)

_module = import_module("entity.pipeline.pipeline")

__all__ = getattr(_module, "__all__", [])


def __getattr__(name: str):
    return getattr(_module, name)
