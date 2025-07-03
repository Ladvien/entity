from __future__ import annotations

from cdktf import App, TerraformStack


class Infrastructure:
    """Simplified wrapper around a Terraform stack."""

    def __init__(self, name: str) -> None:
        self.app = App()
        self.stack = TerraformStack(self.app, name)

    def deploy(self) -> None:
        """Generate Terraform configuration for this stack."""
        self.app.synth()
