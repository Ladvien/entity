from __future__ import annotations

import warnings

<<<<<<< HEAD
from plugins.infrastructure import DockerInfrastructure
=======
from user_plugins.infrastructure.sandbox.runner import DockerSandboxRunner
>>>>>>> 1e2dac3d1112a41dbbaee20650efe1189d1883ea

warnings.warn(
    "pipeline.sandbox.runner is deprecated; use user_plugins.infrastructure.sandbox.runner instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["DockerSandboxRunner"]
