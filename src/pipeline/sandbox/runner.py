from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

warnings.warn(
    (
        "pipeline.sandbox.runner is deprecated; "
        "use user_plugins.infrastructure.sandbox.runner instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from user_plugins.infrastructure.sandbox.runner import DockerSandboxRunner


def __getattr__(name: str):
    if name == "DockerSandboxRunner":
        from user_plugins.infrastructure.sandbox.runner import DockerSandboxRunner

        return DockerSandboxRunner
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["DockerSandboxRunner"]
