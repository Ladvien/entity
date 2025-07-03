from __future__ import annotations

<<<<<<< HEAD
=======
import subprocess
from typing import Type

>>>>>>> fdd01ee24c0cc5f74953ed08a44185415b3acc61
from cdktf import App, TerraformStack


class Infrastructure:
<<<<<<< HEAD
    """Simplified wrapper around a Terraform stack."""

    def __init__(self, name: str) -> None:
        self.app = App()
        self.stack = TerraformStack(self.app, name)

    def deploy(self) -> None:
        """Generate Terraform configuration for this stack."""
        self.app.synth()
=======
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
>>>>>>> fdd01ee24c0cc5f74953ed08a44185415b3acc61
