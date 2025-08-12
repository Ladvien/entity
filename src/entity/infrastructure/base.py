from __future__ import annotations

import logging
from abc import ABC, abstractmethod


class BaseInfrastructure(ABC):
    """Common functionality for infrastructure components."""

    version = "0.1"

    def __init__(self, version: str | None = None) -> None:
        self.version = version or self.version
        self.logger = logging.getLogger(self.__class__.__name__)

    async def startup(self) -> None:
        """Perform asynchronous initialization."""
        self.logger.debug(
            "Starting %s version %s", self.__class__.__name__, self.version
        )

    async def shutdown(self) -> None:
        """Perform asynchronous cleanup."""
        self.logger.debug("Shutting down %s", self.__class__.__name__)

    @abstractmethod
    async def health_check(self) -> bool:
        """Return ``True`` if the infrastructure is healthy."""
        raise NotImplementedError

    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check for compatibility."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return True
            return loop.run_until_complete(self.health_check())
        except Exception:
            return False
