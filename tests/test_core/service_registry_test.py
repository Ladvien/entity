# tests/test_service_registry.py - FIXED VERSION
import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

# Add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.registry import ServiceRegistry, get_memory_system, get_config
from plugins.memory_tools import (
    MemorySearchTool,
    StoreMemoryTool,
    MemorySearchInput,
    StoreMemoryInput,
)


# Pytest fixtures for clean test setup/teardown
@pytest.fixture(autouse=True)
def clean_registry():
    """Automatically clean the ServiceRegistry before and after each test"""
    ServiceRegistry.clear()
    yield
    ServiceRegistry.clear()


@pytest.fixture
def mock_memory_system():
    """Fixture providing a mock memory system"""
    mock = AsyncMock()
    ServiceRegistry.register("memory_system", mock)
    return mock


@pytest.fixture
def mock_config():
    """Fixture providing a mock config"""
    mock = MagicMock()
    ServiceRegistry.register("config", mock)
    return mock


@pytest.fixture
def sample_memory_document():
    """Fixture providing a sample memory document"""
    mock_doc = MagicMock()
    mock_doc.page_content = "Test memory content"
    mock_doc.metadata = {"memory_type": "test", "importance_score": 0.8}
    return mock_doc


# Basic ServiceRegistry functionality tests
class TestServiceRegistry:
    """Test the ServiceRegistry functionality"""

    def test_register_and_get_service(self):
        """Test basic service registration and retrieval"""
        mock_service = MagicMock()
        ServiceRegistry.register("test_service", mock_service)

        retrieved = ServiceRegistry.get("test_service")
        assert retrieved is mock_service

    def test_service_not_found_raises_error(self):
        """Test that getting non-existent service raises helpful error"""
        with pytest.raises(ValueError, match="Service 'nonexistent' not found"):
            ServiceRegistry.get("nonexistent")

    def test_service_already_registered_raises_error(self):
        """Test that registering same service twice raises error"""
        ServiceRegistry.register("test", MagicMock())

        with pytest.raises(ValueError, match="Service 'test' already registered"):
            ServiceRegistry.register("test", MagicMock())

    def test_replace_service(self):
        """Test that replace=True allows overriding services"""
        service1 = MagicMock()
        service2 = MagicMock()

        ServiceRegistry.register("test", service1)
        ServiceRegistry.register("test", service2, replace=True)

        assert ServiceRegistry.get("test") is service2

    def test_list_services(self):
        """Test listing all services"""
        ServiceRegistry.register("service1", MagicMock())
        ServiceRegistry.register("service2", "test_string")

        services = ServiceRegistry.list_services()
        assert "service1" in services
        assert "service2" in services
        assert services["service2"] == "str"  # type name

    def test_has_service(self):
        """Test checking if service exists"""
        assert not ServiceRegistry.has("test")

        ServiceRegistry.register("test", MagicMock())
        assert ServiceRegistry.has("test")

    def test_get_with_default(self):
        """Test getting service with default value"""
        default_value = "default"
        result = ServiceRegistry.get("nonexistent", default_value)
        assert result == default_value

    def test_get_with_none_service(self):
        """Test that None can be registered and retrieved as a service"""
        ServiceRegistry.register("none_service", None)
        result = ServiceRegistry.get("none_service")
        assert result is None

    def test_get_typed_success(self):
        """Test typed service retrieval with correct type"""
        test_string = "hello"
        ServiceRegistry.register("test", test_string)

        result = ServiceRegistry.get_typed("test", str)
        assert result == test_string

    def test_get_typed_wrong_type_raises_error(self):
        """Test typed service retrieval with wrong type"""
        ServiceRegistry.register("test", "string_value")

        with pytest.raises(TypeError, match="Service 'test' is not of type int"):
            ServiceRegistry.get_typed("test", int)

    def test_convenience_functions(self, mock_config, mock_memory_system):
        """Test the convenience getter functions"""
        assert get_config() is mock_config
        assert get_memory_system() is mock_memory_system

    def test_initialization_state(self):
        """Test initialization state tracking"""
        assert not ServiceRegistry.is_initialized()

        ServiceRegistry.mark_initialized()
        assert ServiceRegistry.is_initialized()

        ServiceRegistry.clear()
        assert not ServiceRegistry.is_initialized()


# Memory tools integration tests
class TestMemoryToolsWithServiceRegistry:
    """Test that memory tools work with ServiceRegistry"""

    @pytest.mark.asyncio
    async def test_memory_search_tool_success(
        self, mock_memory_system, sample_memory_document
    ):
        """Test that MemorySearchTool works via ServiceRegistry"""
        # Setup mock response
        mock_memory_system.search_memory.return_value = [sample_memory_document]

        # Test the tool
        tool = MemorySearchTool()
        result = await tool.run(MemorySearchInput(query="test query"))

        # Verify
        assert "Found 1 memories" in result
        assert "Test memory content" in result
        assert "importance: 0.8" in result
        mock_memory_system.search_memory.assert_called_once()

    @pytest.mark.asyncio
    async def test_memory_search_tool_no_results(self, mock_memory_system):
        """Test MemorySearchTool when no memories found"""
        mock_memory_system.search_memory.return_value = []

        tool = MemorySearchTool()
        result = await tool.run(MemorySearchInput(query="nonexistent"))

        assert "No memories found for query: 'nonexistent'" in result

    @pytest.mark.asyncio
    async def test_memory_search_tool_no_memory_system(self):
        """Test graceful failure when memory system not available"""
        # Don't register any memory system
        tool = MemorySearchTool()
        result = await tool.run(MemorySearchInput(query="test"))

        assert "Memory system not available" in result

    @pytest.mark.asyncio
    async def test_memory_search_tool_with_thread_id(
        self, mock_memory_system, sample_memory_document
    ):
        """Test MemorySearchTool with specific thread ID"""
        mock_memory_system.search_memory.return_value = [sample_memory_document]

        tool = MemorySearchTool()
        await tool.run(
            MemorySearchInput(query="test", thread_id="custom_thread", limit=10)
        )

        # Verify the call was made with correct parameters
        call_args = mock_memory_system.search_memory.call_args
        assert call_args[1]["query"] == "test"
        assert call_args[1]["thread_id"] == "custom_thread"
        assert call_args[1]["k"] == 10

    @pytest.mark.asyncio
    async def test_store_memory_tool_success(self, mock_memory_system):
        """Test that StoreMemoryTool works via ServiceRegistry"""
        tool = StoreMemoryTool()
        result = await tool.run(StoreMemoryInput(content="Test content to store"))

        # Verify
        assert "Memory stored successfully" in result
        assert "Test content to store" in result
        mock_memory_system.add_memory.assert_called_once()

        # Check the call arguments
        call_kwargs = mock_memory_system.add_memory.call_args[1]
        assert call_kwargs["content"] == "Test content to store"
        assert call_kwargs["thread_id"] == "default"
        assert call_kwargs["memory_type"] == "observation"
        assert call_kwargs["importance_score"] == 0.5

    @pytest.mark.asyncio
    async def test_store_memory_tool_with_custom_params(self, mock_memory_system):
        """Test StoreMemoryTool with custom parameters"""
        tool = StoreMemoryTool()
        result = await tool.run(
            StoreMemoryInput(
                content="Important memory",
                thread_id="custom_thread",
                memory_type="important",
                importance_score=0.9,
            )
        )

        assert "Memory stored successfully" in result

        # Check the call arguments
        call_kwargs = mock_memory_system.add_memory.call_args[1]
        assert call_kwargs["content"] == "Important memory"
        assert call_kwargs["thread_id"] == "custom_thread"
        assert call_kwargs["memory_type"] == "important"
        assert call_kwargs["importance_score"] == 0.9

    @pytest.mark.asyncio
    async def test_store_memory_tool_no_memory_system(self):
        """Test StoreMemoryTool graceful failure when memory system not available"""
        tool = StoreMemoryTool()
        result = await tool.run(StoreMemoryInput(content="Test content"))

        assert "Memory system not available" in result

    @pytest.mark.asyncio
    async def test_store_memory_tool_exception_handling(self, mock_memory_system):
        """Test StoreMemoryTool error handling"""
        # Make the memory system raise an exception
        mock_memory_system.add_memory.side_effect = Exception("Database error")

        tool = StoreMemoryTool()
        result = await tool.run(StoreMemoryInput(content="Test content"))

        assert "[Error] Failed to store memory: Database error" in result


# Parametrized tests for edge cases
class TestServiceRegistryEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.parametrize(
        "service_name,service_value",
        [
            ("string_service", "hello"),
            ("int_service", 42),
            ("list_service", [1, 2, 3]),
            ("dict_service", {"key": "value"}),
            ("none_service", None),
        ],
    )
    def test_register_different_types(self, service_name, service_value):
        """Test registering different types of services"""
        ServiceRegistry.register(service_name, service_value)
        retrieved = ServiceRegistry.get(service_name)

        # Handle None comparison properly
        if service_value is None:
            assert retrieved is None
        else:
            assert retrieved == service_value

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "",  # empty string
            " ",  # whitespace
            "name with spaces",  # spaces
            "name-with-dashes",  # dashes
            "name.with.dots",  # dots
        ],
    )
    def test_register_with_various_names(self, invalid_name):
        """Test registering services with various name formats"""
        # All names should be allowed - ServiceRegistry is flexible
        ServiceRegistry.register(invalid_name, "test_value")
        assert ServiceRegistry.get(invalid_name) == "test_value"


# Integration tests
class TestServiceRegistryIntegration:
    """Integration tests for real-world usage patterns"""

    def test_multiple_services_interaction(self):
        """Test registering and using multiple services together"""
        config = {"database": {"host": "localhost"}}
        memory = MagicMock()
        storage = MagicMock()

        ServiceRegistry.register("config", config)
        ServiceRegistry.register("memory_system", memory)
        ServiceRegistry.register("storage", storage)

        # Test that all services are accessible
        assert ServiceRegistry.get("config") == config
        assert ServiceRegistry.get("memory_system") == memory
        assert ServiceRegistry.get("storage") == storage

        # Test listing shows all services
        services = ServiceRegistry.list_services()
        assert len(services) == 3
        assert "config" in services
        assert "memory_system" in services
        assert "storage" in services

    @pytest.mark.asyncio
    async def test_service_lifecycle_simulation(self):
        """Test a complete service lifecycle like in the real app"""
        # Simulate app startup
        config = {"app": "test"}
        # Use AsyncMock for proper async shutdown testing
        db = AsyncMock()
        memory = AsyncMock()

        ServiceRegistry.register("config", config)
        ServiceRegistry.register("db_connection", db)
        ServiceRegistry.register("memory_system", memory)
        ServiceRegistry.mark_initialized()

        assert ServiceRegistry.is_initialized()
        assert len(ServiceRegistry.list_services()) == 3

        # Simulate using services
        retrieved_config = get_config()
        retrieved_memory = get_memory_system()

        assert retrieved_config == config
        assert retrieved_memory == memory

        # Simulate shutdown
        await ServiceRegistry.shutdown()
        assert not ServiceRegistry.is_initialized()
        assert len(ServiceRegistry.list_services()) == 0


# Performance tests
class TestServiceRegistryPerformance:
    """Basic performance tests to ensure registry doesn't add significant overhead"""

    def test_service_access_performance(self):
        """Test that service access is fast"""
        import time

        # Register a service
        test_service = {"data": "test"}
        ServiceRegistry.register("perf_test", test_service)

        # Time multiple accesses
        start_time = time.time()
        for _ in range(1000):
            ServiceRegistry.get("perf_test")
        end_time = time.time()

        # Should be very fast (< 0.1 seconds for 1000 accesses)
        assert (end_time - start_time) < 0.1

    def test_many_services_registration(self):
        """Test registering many services doesn't slow down significantly"""
        import time

        start_time = time.time()

        # Register 100 services
        for i in range(100):
            ServiceRegistry.register(f"service_{i}", f"value_{i}")

        end_time = time.time()

        # Should be fast (< 0.1 seconds for 100 registrations)
        assert (end_time - start_time) < 0.1
        assert len(ServiceRegistry.list_services()) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
