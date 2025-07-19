from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from entity.core.plugins import InfrastructurePlugin, ValidationResult
from entity.config.models import DockerConfig


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

    @classmethod
    async def validate_config(cls, config: Dict[str, Any]) -> ValidationResult:
        try:
            DockerConfig(**config)
        except Exception as exc:  # noqa: BLE001
            return ValidationResult.error_result(str(exc))
        return ValidationResult.success_result()

    # ---------------------------------------------------------
    # helpers
    # ---------------------------------------------------------
    def generate_compose(self) -> str:
        """Return full docker-compose configuration."""

        lines = [
            "version: '3.8'",
            "services:",
            "  agent:",
            "    build: .",
            "    container_name: agent",
            "    image: agent:latest",
            "    ports:",
            "      - '8000:8000'",
            "    volumes:",
            "      - agent-data:/data",
            "    networks:",
            "      - agent-net",
            "volumes:",
            "  agent-data:",
            "networks:",
            "  agent-net:",
        ]
        return "\n".join(lines) + "\n"

    async def _execute_impl(self, context: Any) -> None:  # pragma: no cover - stub
        return None

    async def deploy(self) -> None:
        """Write Docker configuration files."""
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "Dockerfile").write_text("FROM python:3.11-slim\n")
        (self.path / "docker-compose.yml").write_text(self.generate_compose())
        self.deployed = True

    async def destroy(self) -> None:
        """Remove generated Docker configuration."""
        for name in ["Dockerfile", "docker-compose.yml"]:
            try:
                (self.path / name).unlink()
            except FileNotFoundError:  # pragma: no cover - best effort cleanup
                pass
        self.deployed = False
