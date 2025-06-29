from __future__ import annotations

import subprocess  # nosec B404
from dataclasses import dataclass
from shutil import which


@dataclass
class PostgresConfig:
    """Configuration for the development PostgreSQL server."""

    user: str = "postgres"
    password: str = "postgres"
    db_name: str = "memory"
    port: int = 5432
    container_name: str = "entity-postgres-dev"


class PostgresDevServer:
    """Utility to manage a local PostgreSQL 17 container."""

    def __init__(self, config: PostgresConfig | None = None) -> None:
        self.config = config or PostgresConfig()

    def start(self) -> None:
        """Start the Docker container in detached mode."""
        docker_exe = which("docker") or "docker"
        command = [
            docker_exe,
            "run",
            "--name",
            self.config.container_name,
            "-e",
            f"POSTGRES_USER={self.config.user}",
            "-e",
            f"POSTGRES_PASSWORD={self.config.password}",
            "-e",
            f"POSTGRES_DB={self.config.db_name}",
            "-p",
            f"{self.config.port}:5432",
            "-d",
            "postgres:17",
        ]
        subprocess.run(command, check=True, shell=False)  # nosec B603 B607

    def stop(self) -> None:
        """Stop and remove the Docker container."""
        docker_exe = which("docker") or "docker"
        subprocess.run(
            [
                docker_exe,
                "rm",
                "-f",
                self.config.container_name,
            ],
            check=True,
            shell=False,  # nosec B603 B607
        )


if __name__ == "__main__":
    PostgresDevServer().start()
