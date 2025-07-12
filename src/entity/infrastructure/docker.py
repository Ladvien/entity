from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from entity.core.plugins import InfrastructurePlugin


class DockerInfrastructure(InfrastructurePlugin):
    """Simple Docker-based infrastructure for local development."""

    name = "docker"
    infrastructure_type = "container"
    resource_category = "infrastructure"
    stages: list = []
    dependencies: list[str] = []

    def __init__(self, config: Dict | None = None) -> None:
        super().__init__(config or {})
        self.path = Path(self.config.get("path", ".")).resolve()
        self.deployed = False

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def deploy(self) -> None:
        """Write Docker configuration files."""
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "Dockerfile").write_text("FROM python:3.11-slim\n")
        (self.path / "docker-compose.yml").write_text(
            "version: '3'\nservices:\n  agent:\n    build: .\n"
        )
        self.deployed = True

    async def destroy(self) -> None:
        """Remove generated Docker configuration."""
        for name in ["Dockerfile", "docker-compose.yml"]:
            try:
                (self.path / name).unlink()
            except FileNotFoundError:  # pragma: no cover - best effort cleanup
                pass
        self.deployed = False
