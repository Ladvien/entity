from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from entity.core.plugins import InfrastructurePlugin


class OpenTofuInfrastructure(InfrastructurePlugin):
    """Base class for OpenTofu-based cloud deployments."""

    infrastructure_type = "cloud"
    resource_category = "infrastructure"
    stages: list = []
    dependencies: list[str] = []

    def __init__(
        self,
        provider: str,
        template: str,
        region: str = "us-east-1",
        config: Dict | None = None,
    ) -> None:
        super().__init__(config or {})
        self.provider = provider
        self.template = template
        self.region = region
        self.path = Path(self.config.get("path", ".")).resolve()
        self.deployed = False

    # ---------------------------------------------------------
    # helpers
    # ---------------------------------------------------------
    def _provider_block(self) -> str:
        return f'provider "{self.provider}" {{\n  region = "{self.region}"\n}}\n'

    def generate_templates(self) -> dict[str, str]:
        """Return Terraform/OpenTofu configuration files."""

        return {"main.tf": self._provider_block()}

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def deploy(self) -> None:
        """Write Terraform/OpenTofu configuration files."""
        self.path.mkdir(parents=True, exist_ok=True)
        for name, content in self.generate_templates().items():
            (self.path / name).write_text(content)
        self.deployed = True

    async def destroy(self) -> None:
        """Remove generated OpenTofu configuration."""
        for name in self.generate_templates().keys():
            try:
                (self.path / name).unlink()
            except FileNotFoundError:  # pragma: no cover - best effort cleanup
                pass
        self.deployed = False
