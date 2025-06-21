# src/core/registry.py - Fixed service type display

import logging
from typing import Dict, Any, Optional, TypeVar, Type

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceRegistry:
    """
    Simple service registry for dependency injection.
    Replaces global variables and manual injection hacks.
    """

    _services: Dict[str, Any] = {}
    _initialized = False

    @classmethod
    def register(cls, name: str, service: Any, replace: bool = False) -> None:
        """Register a service by name"""
        if name in cls._services and not replace:
            raise ValueError(
                f"Service '{name}' already registered. Use replace=True to override."
            )

        cls._services[name] = service
        logger.debug(f"✅ Registered service: {name} ({type(service).__name__})")

    @classmethod
    def get(cls, name: str, default: Any = None) -> Any:
        """Get a service by name"""
        if name not in cls._services:
            if default is None:
                available = list(cls._services.keys())
                raise ValueError(f"Service '{name}' not found. Available: {available}")
            return default
        return cls._services[name]

    @classmethod
    def try_get(cls, name: str):
        """Returns the service if registered, or None if not found."""
        return ServiceRegistry._services.get(name)

    @classmethod
    def get_typed(cls, name: str, service_type: Type[T]) -> T:
        """Get a service with type hints for better IDE support"""
        service = cls.get(name)
        if not isinstance(service, service_type):
            raise TypeError(f"Service '{name}' is not of type {service_type.__name__}")
        return service

    @classmethod
    def has(cls, name: str) -> bool:
        """Check if a service is registered"""
        return name in cls._services

    @classmethod
    def list_services(cls) -> Dict[str, str]:
        """List all registered services with their types"""
        # ✅ FIXED: Properly get the class name
        return {
            name: service.__class__.__name__ for name, service in cls._services.items()
        }

    @classmethod
    def clear(cls) -> None:
        """Clear all services (mainly for testing)"""
        cls._services.clear()
        cls._initialized = False
        logger.debug("🧹 ServiceRegistry cleared")

    @classmethod
    async def shutdown(cls) -> None:
        """Shutdown all services that have cleanup methods"""
        logger.info("🔄 Shutting down services...")

        for name, service in cls._services.items():
            try:
                if hasattr(service, "close"):
                    await service.close()
                    logger.debug(f"✅ Closed service: {name}")
                elif hasattr(service, "shutdown"):
                    await service.shutdown()
                    logger.debug(f"✅ Shutdown service: {name}")
            except Exception as e:
                logger.error(f"❌ Error shutting down service '{name}': {e}")

        cls.clear()
        logger.info("✅ All services shut down")

    @classmethod
    def mark_initialized(cls) -> None:
        """Mark registry as fully initialized"""
        cls._initialized = True
        logger.info(
            f"✅ ServiceRegistry initialized with {len(cls._services)} services"
        )

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if registry is initialized"""
        return cls._initialized


# Convenience functions for common patterns
def get_config():
    """Convenience function to get config"""
    return ServiceRegistry.get("config")


def get_memory_system():
    """Convenience function to get memory system"""
    return ServiceRegistry.get("memory_system")


def get_db_connection():
    """Convenience function to get database connection"""
    return ServiceRegistry.get("db_connection")


def get_tool_manager():
    """Convenience function to get tool manager"""
    return ServiceRegistry.get("tool_manager")


def get_storage():
    """Convenience function to get storage"""
    return ServiceRegistry.get("storage")
