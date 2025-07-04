"""Infrastructure utilities built on Terraform CDK."""

from .infrastructure import Infrastructure

try:  # optional dependency
    from .docker import DockerInfrastructure
except Exception:  # pragma: no cover - missing docker library
    DockerInfrastructure = None  # type: ignore

__all__ = ["Infrastructure", "DockerInfrastructure"]
