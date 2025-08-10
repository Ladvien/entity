"""Type-safe dependency injection system for plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Protocol,
    TypeVar,
    get_type_hints,
    runtime_checkable,
)

from pydantic import BaseModel, ValidationError

from entity.plugins.validation import ValidationResult

if TYPE_CHECKING:
    from entity.plugins.context import PluginContext
    from entity.workflow.workflow import Workflow


# Protocol definitions for type-safe resource injection
@runtime_checkable
class LLMProtocol(Protocol):
    """Protocol for LLM resource interfaces."""

    async def generate(self, prompt: str) -> str:
        """Generate text from a prompt."""
        ...

    def health_check(self) -> bool:
        """Check if the LLM service is healthy."""
        ...


@runtime_checkable
class MemoryProtocol(Protocol):
    """Protocol for Memory resource interfaces."""

    async def store(self, key: str, value: Any) -> None:
        """Store a value with the given key."""
        ...

    async def load(self, key: str, default: Any = None) -> Any:
        """Load a value for the given key, or return default."""
        ...

    def health_check(self) -> bool:
        """Check if the memory service is healthy."""
        ...


@runtime_checkable
class DatabaseProtocol(Protocol):
    """Protocol for Database resource interfaces."""

    def execute(self, query: str, *params: object) -> object:
        """Execute a database query."""
        ...

    def health_check(self) -> bool:
        """Check if the database service is healthy."""
        ...


@runtime_checkable
class VectorStoreProtocol(Protocol):
    """Protocol for Vector Store resource interfaces."""

    def add_vector(self, table: str, vector: object) -> None:
        """Add a vector to the store."""
        ...

    def query(self, query: str) -> object:
        """Query the vector store."""
        ...

    def health_check(self) -> bool:
        """Check if the vector store service is healthy."""
        ...


@runtime_checkable
class LoggingProtocol(Protocol):
    """Protocol for Logging resource interfaces."""

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        """Log a message with the given level."""
        ...

    def health_check(self) -> bool:
        """Check if the logging service is healthy."""
        ...


# Type variable for generic plugin typing
T = TypeVar("T")


class DependencyInjectionContainer:
    """Container for managing type-safe dependency injection."""

    def __init__(self, resources: Dict[str, Any]) -> None:
        """Initialize with resource dictionary."""
        self._resources = resources
        self._type_cache: Dict[str, type] = {}

    def get_resource_by_type(self, resource_type: type[T]) -> T | None:
        """Get a resource by its protocol type."""
        for name, resource in self._resources.items():
            if isinstance(resource, resource_type):
                return resource
        return None

    def validate_dependencies(self, dependencies: Dict[str, type]) -> List[str]:
        """Validate that all required dependencies are available and type-compatible.

        Returns:
            List of missing or incompatible dependencies.
        """
        missing = []

        for dep_name, dep_type in dependencies.items():
            if dep_name not in self._resources:
                missing.append(f"Missing dependency: {dep_name}")
                continue

            resource = self._resources[dep_name]
            if not isinstance(resource, dep_type):
                missing.append(
                    f"Type mismatch for {dep_name}: expected {dep_type.__name__}, "
                    f"got {type(resource).__name__}"
                )

        return missing

    def inject_dependencies(self, dependencies: Dict[str, type]) -> Dict[str, Any]:
        """Inject type-validated dependencies."""
        injected = {}

        for dep_name, dep_type in dependencies.items():
            if dep_name in self._resources:
                resource = self._resources[dep_name]
                if isinstance(resource, dep_type):
                    injected[dep_name] = resource
                else:
                    raise TypeError(
                        f"Type mismatch for {dep_name}: expected {dep_type.__name__}, "
                        f"got {type(resource).__name__}"
                    )
            else:
                raise RuntimeError(f"Missing required dependency: {dep_name}")

        return injected


class TypedPlugin(ABC, Generic[T]):
    """Base class for type-safe plugins with dependency injection."""

    class ConfigModel(BaseModel):
        """Default empty configuration."""

        class Config:
            extra = "forbid"

    supported_stages: List[str] = []
    dependencies: List[str] = []  # Keep for backward compatibility
    skip_conditions: List[Callable[["PluginContext"], bool]] = []

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize with type-safe dependency injection."""
        self.resources = resources
        self.config = config or {}
        self.assigned_stage: str | None = None

        # Initialize dependency injection container
        self._di_container = DependencyInjectionContainer(resources)

        # Validate and inject typed dependencies
        self._validate_and_inject_dependencies()

    @classmethod
    def get_dependencies(cls) -> Dict[str, type]:
        """Return type hints for dependencies.

        This method supports two patterns:
        1. _required_protocols class attribute (convenience classes)
        2. Type hints from __init__ signature (explicit typing)
        """
        # First check if class has _required_protocols defined
        if hasattr(cls, "_required_protocols"):
            return dict(cls._required_protocols)

        try:
            # Get type hints from __init__, excluding 'self', 'resources', and 'config'
            type_hints = get_type_hints(cls.__init__)
            dependencies = {}

            # Filter out non-dependency parameters
            excluded_params = {"self", "resources", "config", "return"}

            for param_name, param_type in type_hints.items():
                if param_name not in excluded_params:
                    dependencies[param_name] = param_type

            return dependencies
        except (AttributeError, TypeError):
            # Fallback to empty dependencies if type hints aren't available
            return {}

    def _validate_and_inject_dependencies(self) -> None:
        """Validate and inject typed dependencies."""
        # Get typed dependencies from class definition
        typed_deps = self.get_dependencies()

        # Validate traditional string-based dependencies for backward compatibility
        if self.dependencies:
            missing_string_deps = [
                dep for dep in self.dependencies if dep not in self.resources
            ]
            if missing_string_deps:
                needed = ", ".join(missing_string_deps)
                raise RuntimeError(
                    f"{self.__class__.__name__} missing required resources: {needed}"
                )

        # Validate typed dependencies
        if typed_deps:
            validation_errors = self._di_container.validate_dependencies(typed_deps)
            if validation_errors:
                error_msg = "; ".join(validation_errors)
                raise RuntimeError(
                    f"{self.__class__.__name__} dependency validation failed: {error_msg}"
                )

            # Inject validated dependencies as instance attributes
            injected = self._di_container.inject_dependencies(typed_deps)
            for dep_name, dep_resource in injected.items():
                setattr(self, dep_name, dep_resource)

    def validate_config(self) -> ValidationResult:
        """Validate configuration using ConfigModel."""
        try:
            self.config = self.ConfigModel(**self.config)
            return ValidationResult.success()
        except ValidationError as exc:
            return ValidationResult.error(str(exc))

    def validate_workflow(self, workflow: "Workflow") -> ValidationResult:
        """Validate that plugin can run in assigned stage."""
        if self.assigned_stage not in workflow.supported_stages:
            return ValidationResult.error(
                f"Workflow does not support stage {self.assigned_stage}"
            )
        return ValidationResult.success()

    def should_execute(self, context: "PluginContext") -> bool:
        """Determine if plugin should run for this context."""
        if hasattr(self, "skip_conditions") and self.skip_conditions:
            for condition in self.skip_conditions:
                if condition(context):
                    return False
        return True

    async def execute(self, context: Any) -> Any:
        """Run the plugin with type safety."""
        if context.current_stage not in self.supported_stages:
            raise RuntimeError(f"Plugin cannot run in {context.current_stage}")

        context._current_plugin_name = self.__class__.__name__
        return await self._execute_impl(context)

    @abstractmethod
    async def _execute_impl(self, context: Any) -> Any:
        """Plugin-specific execution logic."""
        raise NotImplementedError


# Convenience base classes for common dependency patterns
class LLMPlugin(TypedPlugin[LLMProtocol]):
    """Base class for plugins that require LLM access."""

    # Define the required dependencies for automatic injection
    _required_protocols = {"llm": LLMProtocol}

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize with automatic LLM dependency injection."""
        super().__init__(resources, config)
        # LLM will be injected automatically based on _required_protocols


class MemoryPlugin(TypedPlugin[MemoryProtocol]):
    """Base class for plugins that require Memory access."""

    # Define the required dependencies for automatic injection
    _required_protocols = {"memory": MemoryProtocol}

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize with automatic Memory dependency injection."""
        super().__init__(resources, config)
        # Memory will be injected automatically based on _required_protocols


class LLMMemoryPlugin(TypedPlugin[tuple[LLMProtocol, MemoryProtocol]]):
    """Base class for plugins that require both LLM and Memory access."""

    # Define the required dependencies for automatic injection
    _required_protocols = {"llm": LLMProtocol, "memory": MemoryProtocol}

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        """Initialize with automatic LLM and Memory dependency injection."""
        super().__init__(resources, config)
        # LLM and Memory will be injected automatically based on _required_protocols
