from __future__ import annotations

import warnings

warnings.warn(
    (
        "pipeline.sandbox.runner is deprecated; "
        "use plugins.contrib.infrastructure.sandbox.runner instead"
    ),
    DeprecationWarning,
    stacklevel=2,
)


def __getattr__(name: str):
    if name == "DockerSandboxRunner":
        from plugins.contrib.infrastructure.sandbox.runner import DockerSandboxRunner

        return DockerSandboxRunner
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = ["DockerSandboxRunner"]
