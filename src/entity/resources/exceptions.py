"""Custom exceptions used across resources and infrastructure."""


class ResourceError(Exception):
    """Base class for errors raised by resource implementations."""


class InfrastructureError(ResourceError):
    """Raised when infrastructure operations fail."""


class ResourceInitializationError(ResourceError):
    """Raised when a canonical resource is missing required dependencies."""
