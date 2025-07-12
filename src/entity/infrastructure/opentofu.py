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

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def deploy(self) -> None:
        """Write minimal OpenTofu configuration."""
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "main.tf").write_text(f"# {self.provider} {self.template}\n")
        self.deployed = True

    async def destroy(self) -> None:
        """Remove generated OpenTofu configuration."""
        try:
            (self.path / "main.tf").unlink()
        except FileNotFoundError:  # pragma: no cover - best effort cleanup
            pass
        self.deployed = False


class AWSStandardInfrastructure(OpenTofuInfrastructure):
    """Example AWS deployment using the standard template."""

    name = "aws-standard"
    provider = "aws"

    def __init__(self, region: str = "us-east-1", config: Dict | None = None) -> None:
        super().__init__("aws", "standard", region, config)
