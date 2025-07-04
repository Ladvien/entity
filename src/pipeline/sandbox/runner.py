from __future__ import annotations

import warnings

from user_plugins.infrastructure.sandbox.runner import DockerSandboxRunner

warnings.warn(
    "pipeline.sandbox.runner is deprecated; use user_plugins.infrastructure.sandbox.runner instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["DockerSandboxRunner"]
