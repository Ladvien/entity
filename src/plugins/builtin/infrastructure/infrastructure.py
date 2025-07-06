from __future__ import annotations

"""Framework infrastructure helpers using Terraform CDK."""


import subprocess
from typing import Type

try:
    from cdktf import App, TerraformStack
except (ImportError, FileNotFoundError) as exc:  # noqa: WPS440
    raise ImportError(
        "cdktf and Node.js are required for infrastructure features"
    ) from exc


class Infrastructure:
    """Simple wrapper around the Terraform CDK app."""

    def __init__(self) -> None:
        self.app = App()
        self._stack_count = 0

    def add_stack(
        self, stack_cls: Type[TerraformStack], name: str | None = None
    ) -> TerraformStack:
        """Instantiate and register a stack with the app."""
        stack_name = name or f"stack{self._stack_count}"
        self._stack_count += 1
        return stack_cls(self.app, stack_name)

    def synth(self) -> None:
        """Generate Terraform configuration."""
        self.app.synth()

    def deploy(self) -> None:
        """Synthesize and deploy using the ``cdktf`` CLI."""
        self.synth()
        subprocess.run(["cdktf", "deploy", "--auto-approve"], check=True)
