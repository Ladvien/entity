# src/services/application.py
"""
Application service layer that manages the entity agent lifecycle
and provides a clean interface for different components.
"""

import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from src.config import EntitySystemConfig
from src.agent import EntityAgent

# src/exceptions.py
"""
Custom exception classes for better error handling and debugging.
"""


class EntitySystemError(Exception):
    """Base exception for the entity system."""

    pass


class ConfigurationError(EntitySystemError):
    """Raised when there's a configuration error."""

    pass


class EntityAgentError(EntitySystemError):
    """Raised when there's an entity agent error."""

    pass


class MemoryError(EntitySystemError):
    """Raised when there's a memory system error."""

    pass


class APIError(EntitySystemError):
    """Raised when there's an API-related error."""

    pass


logger = logging.getLogger(__name__)


class ApplicationService:
    """
    Central application service that manages the entity agent lifecycle.
    Provides dependency injection and clean separation of concerns.
    """

    def __init__(self, config: EntitySystemConfig):
        self.config = config
        self._entity_agent: Optional[EntityAgent] = None
        self._initialized = False

    @property
    def entity_agent(self) -> EntityAgent:
        """Get the entity agent, raising an error if not initialized."""
        if not self._entity_agent:
            raise EntityAgentError(
                "Entity agent not initialized. Call initialize() first."
            )
        return self._entity_agent

    @property
    def is_initialized(self) -> bool:
        """Check if the application service is initialized."""
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the entity agent and all dependencies."""
        if self._initialized:
            logger.warning("Application service already initialized")
            return

        try:
            logger.info("🚀 Initializing Entity Agent...")
            logger.info(
                f"🤖 Entity: {self.config.entity.name} ({self.config.entity.entity_id})"
            )
            logger.info(
                f"🔧 Database: {self.config.database.host}:{self.config.database.port}"
            )
            logger.info(
                f"🧠 Ollama: {self.config.ollama.base_url} ({self.config.ollama.model})"
            )

            self._entity_agent = EntityAgent(config=self.config)
            await self._entity_agent.initialize()

            self._initialized = True
            logger.info("✅ Entity agent initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize entity agent: {e}")
            await self.cleanup()
            raise EntityAgentError(f"Initialization failed: {e}") from e

    async def cleanup(self) -> None:
        """Clean up resources and shut down the entity agent."""
        if self._entity_agent:
            try:
                await self._entity_agent.close()
                logger.info("✅ Entity agent closed successfully")
            except Exception as e:
                logger.error(f"Error closing entity agent: {e}")
            finally:
                self._entity_agent = None
                self._initialized = False

    async def reload_configuration(self, new_config: EntitySystemConfig) -> None:
        """Reload the configuration and restart the entity agent."""
        logger.info("🔄 Reloading configuration...")
        await self.cleanup()
        self.config = new_config
        await self.initialize()
        logger.info("✅ Configuration reloaded successfully")

    # Business logic methods
    async def process_chat(self, message: str, thread_id: str = "default") -> str:
        """Process a chat message and return the response."""
        return await self.entity_agent.process(message, thread_id)

    async def get_conversation_history(
        self, thread_id: str, limit: int = 10
    ) -> List[str]:
        """Get conversation history for a thread."""
        return await self.entity_agent.get_conversation_history(thread_id, limit)

    async def delete_conversation(self, thread_id: str) -> bool:
        """Delete conversation history for a thread."""
        # This method doesn't exist in your current EntityAgent, so we'll add it
        # For now, return True as a placeholder
        return True

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return await self.entity_agent.get_memory_stats()

    def has_memory(self) -> bool:
        """Check if memory is available."""
        return self.entity_agent.has_memory()

    def get_status(self) -> Dict[str, Any]:
        """Get current application status."""
        return {
            "initialized": self._initialized,
            "entity_name": self.config.entity.name,
            "entity_id": self.config.entity.entity_id,
            "has_memory": self.has_memory() if self._initialized else False,
            "ollama_model": self.config.ollama.model,
            "database_host": self.config.database.host,
            "debug_mode": self.config.debug,
        }


@asynccontextmanager
async def create_application_service(config: EntitySystemConfig):
    """
    Context manager for creating and managing application service lifecycle.
    """
    service = ApplicationService(config)
    try:
        await service.initialize()
        yield service
    finally:
        await service.cleanup()
