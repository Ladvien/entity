# tests/conftest.py
"""
Pytest configuration and shared fixtures for Entity Agent tests
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.registry import ServiceRegistry


@pytest.fixture(autouse=True)
def clean_registry():
    """
    Automatically clean the ServiceRegistry before and after each test.
    This prevents test isolation issues.
    """
    ServiceRegistry.clear()
    yield
    ServiceRegistry.clear()


@pytest.fixture
def mock_config():
    """Fixture providing a mock configuration object"""
    config = MagicMock()
    config.entity.personality.name = "Jade"
    config.entity.personality.sarcasm_level = 0.8
    config.database.host = "localhost"
    config.database.port = 5432
    config.ollama.model = "neural-chat:7b"

    ServiceRegistry.register("config", config)
    return config


@pytest.fixture
def mock_memory_system():
    """Fixture providing a mock memory system"""
    mock = AsyncMock()

    # Configure common mock responses
    mock.get_memory_stats.return_value = {
        "total_memories": 42,
        "status": "active",
        "backend": "pgvector",
    }

    ServiceRegistry.register("memory_system", mock)
    return mock


@pytest.fixture
def mock_db_connection():
    """Fixture providing a mock database connection"""
    mock = AsyncMock()
    mock.test_connection.return_value = True
    mock.ensure_schema.return_value = True
    mock.host = "localhost"
    mock.port = 5432
    mock.schema = "entity"

    ServiceRegistry.register("db_connection", mock)
    return mock


@pytest.fixture
def mock_tool_manager():
    """Fixture providing a mock tool manager"""
    mock = MagicMock()
    mock.list_tool_names.return_value = ["memory_search", "store_memory", "fun_fact"]
    mock.get_all_tools.return_value = []

    ServiceRegistry.register("tool_manager", mock)
    return mock


@pytest.fixture
def mock_storage():
    """Fixture providing a mock storage system"""
    mock = AsyncMock()

    ServiceRegistry.register("storage", mock)
    return mock


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM"""
    mock = AsyncMock()
    mock.ainvoke.return_value = "Mocked LLM response, Thomas."

    ServiceRegistry.register("llm", mock)
    return mock


@pytest.fixture
def mock_output_adapter_manager():
    """Fixture providing a mock output adapter manager"""
    mock = AsyncMock()
    mock.adapters = []
    mock.process_interaction.return_value = (
        MagicMock()
    )  # Return the interaction unchanged

    ServiceRegistry.register("output_adapter_manager", mock)
    return mock


@pytest.fixture
def fully_mocked_registry(
    mock_config,
    mock_memory_system,
    mock_db_connection,
    mock_tool_manager,
    mock_storage,
    mock_llm,
    mock_output_adapter_manager,
):
    """
    Fixture that sets up a fully mocked service registry with all major services.
    Use this when you need to test components that depend on multiple services.
    """
    ServiceRegistry.mark_initialized()
    return ServiceRegistry


@pytest.fixture
def sample_memory_document():
    """Fixture providing a sample memory document for testing"""
    mock_doc = MagicMock()
    mock_doc.page_content = "Test memory content about Thomas and his experiments"
    mock_doc.metadata = {
        "memory_type": "observation",
        "importance_score": 0.8,
        "thread_id": "default",
        "emotional_tone": "neutral",
    }
    return mock_doc


@pytest.fixture
def sample_chat_interaction():
    """Fixture providing a sample ChatInteraction for testing"""
    from src.shared.models import ChatInteraction
    from datetime import datetime

    return ChatInteraction(
        response="A sarcastic response, as you'd expect, Thomas.",
        thread_id="test_thread",
        raw_input="Hello Jade",
        timestamp=datetime.utcnow(),
        raw_output="A sarcastic response, as you'd expect, Thomas.",
        tools_used=["memory_search"],
        memory_context_used=True,
        memory_context="Previous conversation about Thomas's experiments",
        use_tools=True,
        use_memory=True,
        agent_personality_applied=True,
    )


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "asyncio: mark test as an async test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


def pytest_collection_modifyitems(config, items):
    """Automatically mark async tests"""
    for item in items:
        if "async" in item.name or item.function.__name__.startswith("test_async"):
            item.add_marker(pytest.mark.asyncio)


# Helper functions for tests
def create_mock_agent():
    """Helper function to create a mock agent for testing"""
    from src.service.agent import EntityAgent

    mock_agent = AsyncMock(spec=EntityAgent)
    mock_agent.chat.return_value = MagicMock()  # Return a mock ChatInteraction
    return mock_agent


def assert_service_registered(service_name: str):
    """Helper assertion to check if a service is registered"""
    assert ServiceRegistry.has(
        service_name
    ), f"Service '{service_name}' should be registered"


def assert_service_not_registered(service_name: str):
    """Helper assertion to check if a service is not registered"""
    assert not ServiceRegistry.has(
        service_name
    ), f"Service '{service_name}' should not be registered"
