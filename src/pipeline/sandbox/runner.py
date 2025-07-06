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
<<<<<<< HEAD
        from user_plugins.infrastructure.sandbox.runner import DockerSandboxRunner
=======
        from user_plugins.infrastructure.sandbox.runner import \
            DockerSandboxRunner
>>>>>>> 9c565435c8c98d3dd664501aa929f40fe2e70c3f

        return DockerSandboxRunner
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["DockerSandboxRunner"]
