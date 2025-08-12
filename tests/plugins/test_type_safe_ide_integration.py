"""Tests for IDE integration and developer experience with type-safe plugins."""

import inspect
from typing import Any, Dict, get_type_hints

import pytest

from entity.plugins.typed_base import (
    DatabaseProtocol,
    LLMPlugin,
    LLMProtocol,
    MemoryPlugin,
    MemoryProtocol,
    TypedPlugin,
)


class MockLLM:
    """Mock LLM for testing."""

    async def generate(self, prompt: str) -> str:
        return f"Generated: {prompt}"

    def health_check(self) -> bool:
        return True


class MockMemory:
    """Mock Memory for testing."""

    async def store(self, key: str, value: Any) -> None:
        pass

    async def load(self, key: str, default: Any = None) -> Any:
        return default

    def health_check(self) -> bool:
        return True


class TestIDEIntegration:
    """Test IDE integration features like type hints and autocomplete."""

    def test_type_hints_preservation(self):
        """Test that type hints are preserved for IDE support."""

        class TestPlugin(TypedPlugin):
            def __init__(
                self,
                resources: Dict[str, Any],
                config: Dict[str, Any] | None = None,
                *,
                llm: LLMProtocol,
                memory: MemoryProtocol,
            ):
                super().__init__(resources, config)
                self.llm = llm
                self.memory = memory

            async def _execute_impl(self, context: Any) -> str:
                return "test"

        # Get type hints from __init__
        type_hints = get_type_hints(TestPlugin.__init__)

        # Verify type hints exist and are correct
        assert "llm" in type_hints
        assert "memory" in type_hints
        assert type_hints["llm"] is LLMProtocol
        assert type_hints["memory"] is MemoryProtocol

    def test_protocol_methods_discoverable(self):
        """Test that protocol methods are discoverable by IDE."""

        # Get all methods from LLMProtocol
        llm_methods = [
            name for name, method in inspect.getmembers(LLMProtocol, inspect.isfunction)
        ]

        # Check that expected methods exist
        assert "generate" in llm_methods
        assert "health_check" in llm_methods

        # Get all methods from MemoryProtocol
        memory_methods = [
            name
            for name, method in inspect.getmembers(MemoryProtocol, inspect.isfunction)
        ]

        # Check that expected methods exist
        assert "store" in memory_methods
        assert "load" in memory_methods
        assert "health_check" in memory_methods

    def test_method_signatures_accessible(self):
        """Test that method signatures are accessible for IDE autocomplete."""

        # Test LLMProtocol.generate signature
        generate_sig = inspect.signature(LLMProtocol.generate)
        params = list(generate_sig.parameters.keys())

        assert "self" in params
        assert "prompt" in params

        # Check return annotation
        assert generate_sig.return_annotation is str

        # Test MemoryProtocol.store signature
        store_sig = inspect.signature(MemoryProtocol.store)
        params = list(store_sig.parameters.keys())

        assert "self" in params
        assert "key" in params
        assert "value" in params

        # Check return annotation
        assert store_sig.return_annotation is None  # async def returns None

    def test_convenience_class_type_hints(self):
        """Test that convenience classes have proper type hints."""

        class TestLLMPlugin(LLMPlugin):
            async def _execute_impl(self, context: Any) -> str:
                # IDE should provide autocomplete for self.llm methods
                result = await self.llm.generate("test")
                return result

        # Check that the plugin has typed llm attribute
        resources = {"llm": MockLLM()}
        plugin = TestLLMPlugin(resources, {})

        # Verify attribute exists and has correct type
        assert hasattr(plugin, "llm")
        assert isinstance(plugin.llm, LLMProtocol)

    def test_multiple_protocol_inheritance(self):
        """Test type hints work with multiple protocol dependencies."""

        class MockDatabase:
            def execute(self, query: str, *params: object) -> object:
                return None

            def health_check(self) -> bool:
                return True

        class MultiProtocolPlugin(TypedPlugin):
            def __init__(
                self,
                resources: Dict[str, Any],
                config: Dict[str, Any] | None = None,
                *,
                llm: LLMProtocol,
                memory: MemoryProtocol,
                database: DatabaseProtocol,
            ):
                super().__init__(resources, config)
                self.llm = llm
                self.memory = memory
                self.database = database

            async def _execute_impl(self, context: Any) -> str:
                # IDE should provide autocomplete for all protocols
                response = await self.llm.generate("test")
                await self.memory.store("key", response)
                self.database.execute("SELECT 1")
                return response

        resources = {
            "llm": MockLLM(),
            "memory": MockMemory(),
            "database": MockDatabase(),
        }

        plugin = MultiProtocolPlugin(resources, {})

        # Verify all attributes are typed correctly
        assert isinstance(plugin.llm, LLMProtocol)
        assert isinstance(plugin.memory, MemoryProtocol)
        assert isinstance(plugin.database, DatabaseProtocol)


class TestDeveloperExperience:
    """Test developer experience improvements."""

    def test_clear_initialization_pattern(self):
        """Test that initialization pattern is clear and consistent."""

        class ExamplePlugin(TypedPlugin):
            def __init__(
                self,
                resources: Dict[str, Any],
                config: Dict[str, Any] | None = None,
                *,  # This forces keyword-only arguments for dependencies
                llm: LLMProtocol,
                memory: MemoryProtocol,
            ):
                super().__init__(resources, config)
                self.llm = llm
                self.memory = memory

            async def _execute_impl(self, context: Any) -> str:
                return "test"

        # Verify the pattern works
        resources = {"llm": MockLLM(), "memory": MockMemory()}
        plugin = ExamplePlugin(resources, {})

        assert plugin.llm is not None
        assert plugin.memory is not None

    def test_dependency_discovery_method(self):
        """Test that developers can easily discover dependencies."""

        class DiscoverablePlugin(TypedPlugin):
            def __init__(
                self,
                resources: Dict[str, Any],
                config: Dict[str, Any] | None = None,
                *,
                llm: LLMProtocol,
                memory: MemoryProtocol,
            ):
                super().__init__(resources, config)
                self.llm = llm
                self.memory = memory

            async def _execute_impl(self, context: Any) -> str:
                return "test"

        # Developers can call get_dependencies() to see what's needed
        deps = DiscoverablePlugin.get_dependencies()

        assert "llm" in deps
        assert "memory" in deps
        assert deps["llm"] is LLMProtocol
        assert deps["memory"] is MemoryProtocol

    def test_error_messages_developer_friendly(self):
        """Test that error messages guide developers to solutions."""

        class PluginWithDeps(TypedPlugin):
            def __init__(
                self,
                resources: Dict[str, Any],
                config: Dict[str, Any] | None = None,
                *,
                llm: LLMProtocol,
                missing_resource: MemoryProtocol,
            ):
                super().__init__(resources, config)
                self.llm = llm
                self.missing_resource = missing_resource

            async def _execute_impl(self, context: Any) -> str:
                return "test"

        # Try to initialize with missing resource
        resources = {"llm": MockLLM()}  # Missing memory resource

        with pytest.raises(RuntimeError) as exc_info:
            PluginWithDeps(resources, {})

        error_message = str(exc_info.value)

        # Error message should be helpful
        assert "dependency validation failed" in error_message
        assert "Missing dependency: missing_resource" in error_message

    def test_backward_compatibility_clear(self):
        """Test that backward compatibility is clear and works."""

        class BackwardCompatiblePlugin(TypedPlugin):
            # Old-style dependency declaration
            dependencies = ["legacy_resource"]

            def __init__(
                self,
                resources: Dict[str, Any],
                config: Dict[str, Any] | None = None,
                *,
                llm: LLMProtocol,  # New-style typed dependency
            ):
                super().__init__(resources, config)
                self.llm = llm
                # Old-style access pattern still works
                self.legacy = self.resources["legacy_resource"]

            async def _execute_impl(self, context: Any) -> str:
                return f"New: {await self.llm.generate('test')}, Old: {self.legacy}"

        resources = {"llm": MockLLM(), "legacy_resource": "legacy_value"}

        plugin = BackwardCompatiblePlugin(resources, {})

        # Both patterns work
        assert isinstance(plugin.llm, LLMProtocol)
        assert plugin.legacy == "legacy_value"

    def test_protocol_extensibility(self):
        """Test that developers can extend protocols for custom resources."""

        from typing import Protocol, runtime_checkable

        @runtime_checkable
        class CustomResourceProtocol(Protocol):
            """Custom resource protocol for testing."""

            def custom_method(self, data: str) -> dict:
                """Custom method signature."""
                ...

            def health_check(self) -> bool:
                """Standard health check."""
                ...

        class MockCustomResource:
            """Mock implementation of custom protocol."""

            def custom_method(self, data: str) -> dict:
                return {"processed": data}

            def health_check(self) -> bool:
                return True

        class CustomPlugin(TypedPlugin):
            def __init__(
                self,
                resources: Dict[str, Any],
                config: Dict[str, Any] | None = None,
                *,
                custom: CustomResourceProtocol,
            ):
                super().__init__(resources, config)
                self.custom = custom

            async def _execute_impl(self, context: Any) -> dict:
                return self.custom.custom_method("test")

        # Test that custom protocol works
        custom_resource = MockCustomResource()
        assert isinstance(custom_resource, CustomResourceProtocol)

        resources = {"custom": custom_resource}
        plugin = CustomPlugin(resources, {})

        assert plugin.custom is custom_resource

    def test_mypy_compatibility(self):
        """Test patterns that work well with mypy type checking."""

        class MyPyFriendlyPlugin(TypedPlugin):
            """Plugin designed to work well with mypy."""

            def __init__(
                self,
                resources: Dict[str, Any],
                config: Dict[str, Any] | None = None,
                *,
                llm: LLMProtocol,
                memory: MemoryProtocol,
            ):
                super().__init__(resources, config)
                self.llm = llm
                self.memory = memory

            async def _execute_impl(self, context: Any) -> str:
                # These method calls should be type-safe for mypy
                prompt: str = "test prompt"
                response: str = await self.llm.generate(prompt)

                key: str = "response_key"
                await self.memory.store(key, response)

                retrieved: str = await self.memory.load(key, "default")

                return retrieved

        resources = {"llm": MockLLM(), "memory": MockMemory()}
        plugin = MyPyFriendlyPlugin(resources, {})

        # Plugin should work correctly
        assert plugin.llm is not None
        assert plugin.memory is not None


class TestDocumentationGeneration:
    """Test that the type system generates good documentation."""

    def test_plugin_dependencies_self_documenting(self):
        """Test that plugin dependencies are self-documenting."""

        class WellDocumentedPlugin(TypedPlugin):
            """A well-documented plugin showing type-safe patterns.

            This plugin demonstrates how type hints make dependencies
            self-documenting and provide IDE support.
            """

            def __init__(
                self,
                resources: Dict[str, Any],
                config: Dict[str, Any] | None = None,
                *,
                llm: LLMProtocol,  # Required: LLM for text generation
                memory: MemoryProtocol,  # Required: Memory for persistence
            ):
                """Initialize with typed dependencies.

                Args:
                    resources: Resource dictionary
                    config: Optional plugin configuration
                    llm: LLM resource for text generation
                    memory: Memory resource for data persistence
                """
                super().__init__(resources, config)
                self.llm = llm
                self.memory = memory

            async def _execute_impl(self, context: Any) -> str:
                """Execute plugin logic with full type safety."""
                return "documented"

        # Documentation should be accessible
        assert WellDocumentedPlugin.__doc__ is not None
        assert "type-safe patterns" in WellDocumentedPlugin.__doc__

        # Method documentation should be accessible
        assert WellDocumentedPlugin.__init__.__doc__ is not None
        assert "typed dependencies" in WellDocumentedPlugin.__init__.__doc__

    def test_protocol_documentation(self):
        """Test that protocols are well-documented for developers."""

        # Protocols should have clear docstrings
        assert LLMProtocol.__doc__ is not None
        assert "LLM resource" in LLMProtocol.__doc__

        assert MemoryProtocol.__doc__ is not None
        assert "Memory resource" in MemoryProtocol.__doc__

        # Protocol methods should be documented
        assert hasattr(LLMProtocol, "generate")
        assert hasattr(MemoryProtocol, "store")
        assert hasattr(MemoryProtocol, "load")

    def test_convenience_class_documentation(self):
        """Test that convenience classes have helpful documentation."""

        # Check that convenience classes have docstrings
        assert LLMPlugin.__doc__ is not None
        assert "LLM access" in LLMPlugin.__doc__

        assert MemoryPlugin.__doc__ is not None
        assert "Memory access" in MemoryPlugin.__doc__
