from __future__ import annotations

"""Framework infrastructure helpers using Terraform CDK."""


import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Type

try:
    from cdktf import App, TerraformStack

    CDKTF_AVAILABLE = True
except (ImportError, FileNotFoundError):  # noqa: WPS440
    App = TerraformStack = None
    CDKTF_AVAILABLE = False

ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _interpolate(value: Any) -> Any:
    """Recursively replace ``${VAR}`` patterns with environment values."""

    if isinstance(value, str):

        def _replace(match: re.Match[str]) -> str:
            return os.getenv(match.group(1), match.group(0))

        return ENV_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v) for v in value]
    return value


class Infrastructure:
    """Simple wrapper around the Terraform CDK app."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.app = App() if CDKTF_AVAILABLE else None
        self._stack_count = 0
        self.config: Dict[str, Any] = _interpolate(config or {})

    def _require_cdktf(self) -> None:
        if not CDKTF_AVAILABLE:
            raise RuntimeError(
                "cdktf and Node.js are required for infrastructure features"
            )

    def add_stack(
        self, stack_cls: Type[TerraformStack], name: str | None = None
    ) -> TerraformStack:
        """Instantiate and register a stack with the app."""
        self._require_cdktf()
        stack_name = name or f"stack{self._stack_count}"
        self._stack_count += 1
        return stack_cls(self.app, stack_name)

    def synth(self) -> None:
        """Generate Terraform configuration."""
        self._require_cdktf()
        self.app.synth()

    def deploy(self) -> None:
        """Synthesize and deploy using the ``cdktf`` CLI."""
        self._require_cdktf()
        self.synth()
        command = shutil.which("cdktf")
        if command is None:
            raise FileNotFoundError("cdktf CLI not found")
        subprocess.run([command, "deploy", "--auto-approve"], check=True)

    def plan(self) -> None:
        """Run ``terraform plan`` in the configured working directory."""
        self._require_cdktf()
        command = shutil.which("terraform")
        if command is None:
            raise FileNotFoundError("Terraform CLI not found")
        working_dir = Path(self.config.get("terraform", {}).get("working_dir", "."))
        variables = self.config.get("terraform", {}).get("variables", {})
        var_args = [f"-var={k}={v}" for k, v in variables.items()]
        subprocess.run([command, "init"], cwd=working_dir, check=True)
        subprocess.run([command, "plan", *var_args], cwd=working_dir, check=True)
