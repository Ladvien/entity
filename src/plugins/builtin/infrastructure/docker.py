from __future__ import annotations

"""Helpers for containerizing agents with Docker."""


from typing import Dict

import docker


class DockerInfrastructure:
    """Build and run Docker images for the agent."""

    def __init__(self, base_image: str = "python:3.11-slim") -> None:
        self.client = docker.from_env()
        self.base_image = base_image

    def build_image(
        self, context: str, tag: str = "agent:latest", dockerfile: str = "Dockerfile"
    ) -> None:
        """Build a Docker image from ``context``."""
        self.client.images.build(path=context, tag=tag, dockerfile=dockerfile)

    def run_container(
        self,
        image: str,
        command: list[str],
        *,
        cpu: float = 1.0,
        memory: str = "512m",
        volumes: Dict[str, Dict[str, str]] | None = None,
    ) -> None:
        """Run a container with resource limits."""
        self.client.containers.run(
            image,
            command=command,
            volumes=volumes or {},
            cpus=cpu,
            mem_limit=memory,
            remove=True,
        )
