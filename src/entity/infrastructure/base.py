from __future__ import annotations

import logging
from abc import ABC, abstractmethod


class BaseInfrastructure(ABC):
    """Common functionality for infrastructure components."""

    version = "0.1"

    def __init__(self, version: str | None = None) -> None:
        self.version = version or self.version
        self.logger = logging.getLogger(self.__class__.__name__)

    async def startup(self) -> None:  # pragma: no cover - thin wrapper
        """Perform asynchronous initialization."""
        self.logger.debug(
            "Starting %s version %s", self.__class__.__name__, self.version
        )

    async def shutdown(self) -> None:  # pragma: no cover - thin wrapper
        """Perform asynchronous cleanup."""
        self.logger.debug("Shutting down %s", self.__class__.__name__)

    @abstractmethod
    def health_check(self) -> bool:
        """Return ``True`` if the infrastructure is healthy."""
        raise NotImplementedError
