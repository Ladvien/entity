"""Tests for type-safe dependency injection system."""

from typing import Any, Dict
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, Field

from entity.plugins.typed_base import (
    DatabaseProtocol,
    DependencyInjectionContainer,
    LLMMemoryPlugin,
    LLMPlugin,
    LLMProtocol,
    LoggingProtocol,
    MemoryPlugin,
    MemoryProtocol,
    TypedPlugin,
    VectorStoreProtocol,
)


# Mock resource implementations
class MockLLM:
    """Mock LLM resource that implements LLMProtocol."""

    def __init__(self, response: str = "mock response"):
        self.response = response
        self._healthy = True

    async def generate(self, prompt: str) -> str:
        return f"{self.response} for: {prompt}"

    def health_check(self) -> bool:
        return self._healthy


class MockMemory:
    """Mock Memory resource that implements MemoryProtocol."""

    def __init__(self):
        self._storage: Dict[str, Any] = {}
        self._healthy = True

    async def store(self, key: str, value: Any) -> None:
        self._storage[key] = value

    async def load(self, key: str, default: Any = None) -> Any:
        return self._storage.get(key, default)

    def health_check(self) -> bool:
        return self._healthy


class MockDatabase:
    """Mock Database resource that implements DatabaseProtocol."""

    def __init__(self):
        self._healthy = True
        self.executed_queries = []

    def execute(self, query: str, *params: object) -> object:
        self.executed_queries.append((query, params))
        return Mock()

    def health_check(self) -> bool:
        return self._healthy


class MockVectorStore:
    """Mock VectorStore resource that implements VectorStoreProtocol."""

    def __init__(self):
        self._healthy = True
        self.vectors = []
        self.queries = []

    def add_vector(self, table: str, vector: object) -> None:
        self.vectors.append((table, vector))

    def query(self, query: str) -> object:
        self.queries.append(query)
        return Mock()

    def health_check(self) -> bool:
        return self._healthy


class MockLogging:
    """Mock Logging resource that implements LoggingProtocol."""

    def __init__(self):
        self._healthy = True
        self.logs = []

    def log(self, level: str, message: str, **kwargs: Any) -> None:
        self.logs.append((level, message, kwargs))

    def health_check(self) -> bool:
        return self._healthy


# Test plugin implementations
class TestTypedPlugin(TypedPlugin):
    """Test plugin with multiple typed dependencies."""

    supported_stages = ["test"]
    _required_protocols = {
        "llm": LLMProtocol,
        "memory": MemoryProtocol,
        "database": DatabaseProtocol,
    }

    async def _execute_impl(self, context: Any) -> str:
        response = await self.llm.generate("test")
        await self.memory.store("response", response)
        self.database.execute("INSERT INTO test VALUES (?)", response)
        return response


class TestLLMOnlyPlugin(LLMPlugin):
    """Test plugin using LLM convenience base class."""

    supported_stages = ["test"]

    async def _execute_impl(self, context: Any) -> str:
        return await self.llm.generate("test")


class TestMemoryOnlyPlugin(MemoryPlugin):
    """Test plugin using Memory convenience base class."""

    supported_stages = ["test"]

    async def _execute_impl(self, context: Any) -> str:
        await self.memory.store("test", "value")
        return await self.memory.load("test")


class TestLLMMemoryPlugin(LLMMemoryPlugin):
    """Test plugin using LLMMemory convenience base class."""

    supported_stages = ["test"]

    async def _execute_impl(self, context: Any) -> str:
        response = await self.llm.generate("test")
        await self.memory.store("response", response)
        return response


class TestIncompatiblePlugin(TypedPlugin):
    """Test plugin with dependencies that won't match resources."""

    _required_protocols = {
        "nonexistent": str,  # Wrong type - str is not a protocol
    }

    async def _execute_impl(self, context: Any) -> str:
        return "test"


class TestHybridPlugin(TypedPlugin):
    """Test plugin mixing old string-based and new typed dependencies."""

    dependencies = ["old_resource"]  # Old-style dependency
    supported_stages = ["test"]
    _required_protocols = {
        "llm": LLMProtocol,  # New-style typed dependency
    }

    def __init__(self, resources: Dict[str, Any], config: Dict[str, Any] | None = None):
        super().__init__(resources, config)
        # Old-style access
        self.old_resource = self.resources["old_resource"]

    async def _execute_impl(self, context: Any) -> str:
        response = await self.llm.generate("test")
        return f"{self.old_resource} + {response}"


class TestProtocolCompliance:
    """Test that mock resources implement protocols correctly."""

    def test_mock_llm_protocol_compliance(self):
        """Test that MockLLM implements LLMProtocol."""
        mock_llm = MockLLM()
        assert isinstance(mock_llm, LLMProtocol)

    def test_mock_memory_protocol_compliance(self):
        """Test that MockMemory implements MemoryProtocol."""
        mock_memory = MockMemory()
        assert isinstance(mock_memory, MemoryProtocol)

    def test_mock_database_protocol_compliance(self):
        """Test that MockDatabase implements DatabaseProtocol."""
        mock_db = MockDatabase()
        assert isinstance(mock_db, DatabaseProtocol)

    def test_mock_vector_store_protocol_compliance(self):
        """Test that MockVectorStore implements VectorStoreProtocol."""
        mock_vs = MockVectorStore()
        assert isinstance(mock_vs, VectorStoreProtocol)

    def test_mock_logging_protocol_compliance(self):
        """Test that MockLogging implements LoggingProtocol."""
        mock_log = MockLogging()
        assert isinstance(mock_log, LoggingProtocol)


class TestDependencyInjectionContainer:
    """Test the dependency injection container."""

    def setup_method(self):
        """Set up test resources."""
        self.mock_llm = MockLLM()
        self.mock_memory = MockMemory()
        self.mock_db = MockDatabase()

        self.resources = {
            "llm": self.mock_llm,
            "memory": self.mock_memory,
            "database": self.mock_db,
        }

        self.container = DependencyInjectionContainer(self.resources)

    def test_get_resource_by_type(self):
        """Test getting resources by protocol type."""
        llm = self.container.get_resource_by_type(LLMProtocol)
        assert llm is self.mock_llm

        memory = self.container.get_resource_by_type(MemoryProtocol)
        assert memory is self.mock_memory

        db = self.container.get_resource_by_type(DatabaseProtocol)
        assert db is self.mock_db

    def test_get_nonexistent_resource(self):
        """Test getting a resource type that doesn't exist."""
        result = self.container.get_resource_by_type(VectorStoreProtocol)
        assert result is None

    def test_validate_dependencies_success(self):
        """Test successful dependency validation."""
        dependencies = {
            "llm": LLMProtocol,
            "memory": MemoryProtocol,
            "database": DatabaseProtocol,
        }

        errors = self.container.validate_dependencies(dependencies)
        assert errors == []

    def test_validate_dependencies_missing(self):
        """Test validation with missing dependency."""
        dependencies = {
            "llm": LLMProtocol,
            "nonexistent": MemoryProtocol,
        }

        errors = self.container.validate_dependencies(dependencies)
        assert len(errors) == 1
        assert "Missing dependency: nonexistent" in errors[0]

    def test_validate_dependencies_type_mismatch(self):
        """Test validation with type mismatch."""
        # Add a string instead of a protocol-compliant resource
        self.resources["bad_resource"] = "not a protocol"
        container = DependencyInjectionContainer(self.resources)

        dependencies = {
            "bad_resource": LLMProtocol,
        }

        errors = container.validate_dependencies(dependencies)
        assert len(errors) == 1
        assert "Type mismatch for bad_resource" in errors[0]

    def test_inject_dependencies_success(self):
        """Test successful dependency injection."""
        dependencies = {
            "llm": LLMProtocol,
            "memory": MemoryProtocol,
        }

        injected = self.container.inject_dependencies(dependencies)

        assert injected["llm"] is self.mock_llm
        assert injected["memory"] is self.mock_memory
        assert len(injected) == 2

    def test_inject_dependencies_missing(self):
        """Test injection with missing dependency."""
        dependencies = {
            "nonexistent": LLMProtocol,
        }

        with pytest.raises(
            RuntimeError, match="Missing required dependency: nonexistent"
        ):
            self.container.inject_dependencies(dependencies)

    def test_inject_dependencies_type_mismatch(self):
        """Test injection with type mismatch."""
        self.resources["bad_resource"] = "not a protocol"
        container = DependencyInjectionContainer(self.resources)

        dependencies = {
            "bad_resource": LLMProtocol,
        }

        with pytest.raises(TypeError, match="Type mismatch for bad_resource"):
            container.inject_dependencies(dependencies)


class TestTypedPluginSystem:
    """Test the typed plugin system."""

    def setup_method(self):
        """Set up test resources."""
        self.mock_llm = MockLLM("test response")
        self.mock_memory = MockMemory()
        self.mock_db = MockDatabase()

        self.resources = {
            "llm": self.mock_llm,
            "memory": self.mock_memory,
            "database": self.mock_db,
            "old_resource": "legacy value",
        }

    def test_typed_plugin_initialization_success(self):
        """Test successful initialization of typed plugin."""
        plugin = TestTypedPlugin(self.resources, {})

        # Check that dependencies were injected
        assert plugin.llm is self.mock_llm
        assert plugin.memory is self.mock_memory
        assert plugin.database is self.mock_db

        # Check that resources dict is still available
        assert plugin.resources is self.resources

    def test_typed_plugin_initialization_missing_dependency(self):
        """Test initialization failure with missing dependency."""
        resources_missing = {
            "llm": self.mock_llm,
            # Missing memory and database
        }

        with pytest.raises(RuntimeError, match="dependency validation failed"):
            TestTypedPlugin(resources_missing, {})

    def test_typed_plugin_initialization_wrong_type(self):
        """Test initialization failure with wrong resource type."""
        resources_wrong_type = {
            "llm": "not an llm",  # Wrong type
            "memory": self.mock_memory,
            "database": self.mock_db,
        }

        with pytest.raises(RuntimeError, match="dependency validation failed"):
            TestTypedPlugin(resources_wrong_type, {})

    @pytest.mark.asyncio
    async def test_typed_plugin_execution(self):
        """Test execution of typed plugin."""
        plugin = TestTypedPlugin(self.resources, {})

        # Mock context
        context = Mock()
        context.current_stage = "test"

        # Execute plugin
        result = await plugin.execute(context)

        # Check result
        assert "test response for: test" in result

        # Check that memory was used
        stored_response = await self.mock_memory.load("response")
        assert stored_response == result

        # Check that database was used
        assert len(self.mock_db.executed_queries) == 1
        query, params = self.mock_db.executed_queries[0]
        assert "INSERT INTO test VALUES" in query
        assert params[0] == result

    def test_get_dependencies_method(self):
        """Test that get_dependencies returns correct type hints."""
        dependencies = TestTypedPlugin.get_dependencies()

        expected = {
            "llm": LLMProtocol,
            "memory": MemoryProtocol,
            "database": DatabaseProtocol,
        }

        assert dependencies == expected

    def test_hybrid_plugin_compatibility(self):
        """Test that old and new dependency styles work together."""
        plugin = TestHybridPlugin(self.resources, {})

        # Check new-style dependency
        assert plugin.llm is self.mock_llm

        # Check old-style dependency
        assert plugin.old_resource == "legacy value"

    def test_hybrid_plugin_missing_old_dependency(self):
        """Test hybrid plugin fails if old-style dependency is missing."""
        resources_no_old = {
            "llm": self.mock_llm,
            # Missing old_resource
        }

        with pytest.raises(
            RuntimeError, match="missing required resources: old_resource"
        ):
            TestHybridPlugin(resources_no_old, {})

    def test_incompatible_plugin_initialization(self):
        """Test that incompatible plugin fails initialization."""
        with pytest.raises(RuntimeError, match="dependency validation failed"):
            TestIncompatiblePlugin(self.resources, {})


class TestConvenienceBaseClasses:
    """Test convenience base classes for common patterns."""

    def setup_method(self):
        """Set up test resources."""
        self.mock_llm = MockLLM("convenience response")
        self.mock_memory = MockMemory()

        self.resources = {
            "llm": self.mock_llm,
            "memory": self.mock_memory,
        }

    def test_llm_plugin_initialization(self):
        """Test LLMPlugin convenience base class."""
        plugin = TestLLMOnlyPlugin(self.resources, {})

        assert plugin.llm is self.mock_llm
        assert hasattr(plugin, "resources")

    def test_memory_plugin_initialization(self):
        """Test MemoryPlugin convenience base class."""
        plugin = TestMemoryOnlyPlugin(self.resources, {})

        assert plugin.memory is self.mock_memory
        assert hasattr(plugin, "resources")

    def test_llm_memory_plugin_initialization(self):
        """Test LLMMemoryPlugin convenience base class."""
        plugin = TestLLMMemoryPlugin(self.resources, {})

        assert plugin.llm is self.mock_llm
        assert plugin.memory is self.mock_memory
        assert hasattr(plugin, "resources")

    @pytest.mark.asyncio
    async def test_llm_plugin_execution(self):
        """Test LLMPlugin execution."""
        plugin = TestLLMOnlyPlugin(self.resources, {})

        context = Mock()
        context.current_stage = "test"

        result = await plugin.execute(context)
        assert "convenience response for: test" in result

    @pytest.mark.asyncio
    async def test_memory_plugin_execution(self):
        """Test MemoryPlugin execution."""
        plugin = TestMemoryOnlyPlugin(self.resources, {})

        context = Mock()
        context.current_stage = "test"

        result = await plugin.execute(context)
        assert result == "value"

        # Check that value was stored
        stored = await self.mock_memory.load("test")
        assert stored == "value"

    @pytest.mark.asyncio
    async def test_llm_memory_plugin_execution(self):
        """Test LLMMemoryPlugin execution."""
        plugin = TestLLMMemoryPlugin(self.resources, {})

        context = Mock()
        context.current_stage = "test"

        result = await plugin.execute(context)
        assert "convenience response for: test" in result

        # Check that response was stored in memory
        stored = await self.mock_memory.load("response")
        assert stored == result


class TestConfigurationValidation:
    """Test configuration validation with typed plugins."""

    def test_config_validation_success(self):
        """Test successful configuration validation."""
        mock_llm = MockLLM()
        resources = {"llm": mock_llm}

        class ConfigurablePlugin(LLMPlugin):
            class ConfigModel(BaseModel):
                max_tokens: int = Field(default=100, gt=0)
                temperature: float = Field(default=0.7, ge=0.0, le=1.0)

            async def _execute_impl(self, context):
                return "test"

        config = {"max_tokens": 50, "temperature": 0.5}
        plugin = ConfigurablePlugin(resources, config)

        validation_result = plugin.validate_config()
        assert validation_result.success
        assert plugin.config.max_tokens == 50
        assert plugin.config.temperature == 0.5

    def test_config_validation_failure(self):
        """Test configuration validation failure."""
        mock_llm = MockLLM()
        resources = {"llm": mock_llm}

        class ConfigurablePlugin(LLMPlugin):
            class ConfigModel(BaseModel):
                max_tokens: int = Field(gt=0)

            async def _execute_impl(self, context):
                return "test"

        config = {"max_tokens": -1}  # Invalid value
        plugin = ConfigurablePlugin(resources, config)

        validation_result = plugin.validate_config()
        assert not validation_result.success
        assert len(validation_result.errors) > 0
        assert "greater than 0" in validation_result.errors[0]


class TestHealthChecking:
    """Test health checking functionality."""

    def test_resource_health_checks(self):
        """Test that resource health checks work."""
        mock_llm = MockLLM()
        mock_memory = MockMemory()

        assert mock_llm.health_check() is True
        assert mock_memory.health_check() is True

        # Test unhealthy resources
        mock_llm._healthy = False
        mock_memory._healthy = False

        assert mock_llm.health_check() is False
        assert mock_memory.health_check() is False

    def test_plugin_health_validation(self):
        """Test plugin can validate resource health."""
        mock_llm = MockLLM()
        mock_memory = MockMemory()
        resources = {"llm": mock_llm, "memory": mock_memory}

        class HealthAwarePlugin(LLMMemoryPlugin):
            def validate_health(self) -> bool:
                return self.llm.health_check() and self.memory.health_check()

            async def _execute_impl(self, context):
                return "test"

        plugin = HealthAwarePlugin(resources, {})

        # Test healthy resources
        assert plugin.validate_health() is True

        # Test unhealthy LLM
        mock_llm._healthy = False
        assert plugin.validate_health() is False

        # Reset LLM, make memory unhealthy
        mock_llm._healthy = True
        mock_memory._healthy = False
        assert plugin.validate_health() is False


class TestErrorHandling:
    """Test error handling in type-safe system."""

    def test_clear_error_messages(self):
        """Test that error messages are clear and helpful."""
        resources = {
            "llm": "not an llm protocol",
            "memory": MockMemory(),
            "database": MockDatabase(),
        }

        try:
            TestTypedPlugin(resources, {})
            assert False, "Should have raised error"
        except RuntimeError as e:
            error_msg = str(e)
            assert "dependency validation failed" in error_msg
            assert "Type mismatch for llm" in error_msg
            assert "expected LLMProtocol" in error_msg

    def test_missing_dependency_error(self):
        """Test clear error for missing dependencies."""
        resources = {
            "llm": MockLLM(),
            # Missing memory and database
        }

        try:
            TestTypedPlugin(resources, {})
            assert False, "Should have raised error"
        except RuntimeError as e:
            error_msg = str(e)
            assert "dependency validation failed" in error_msg
            assert "Missing dependency: memory" in error_msg
            assert "Missing dependency: database" in error_msg
