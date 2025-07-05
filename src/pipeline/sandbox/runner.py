from __future__ import annotations

import warnings

from plugins.contrib.infrastructure.sandbox.runner import DockerSandboxRunner

warnings.warn(
    "pipeline.sandbox.runner is deprecated; use plugins.contrib.infrastructure.sandbox.runner instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["DockerSandboxRunner"]
