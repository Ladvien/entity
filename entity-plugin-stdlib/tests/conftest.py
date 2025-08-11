"""
Test configuration and fixtures.
"""

import sys
from unittest.mock import Mock

import pytest


# Mock the entity-core imports
class MockBasePlugin:
    """Mock BasePlugin for testing."""

    def __init__(self, config=None):
        self.config = config or {}
        self.logger = Mock()
        self.logger.info = Mock()
        self.logger.error = Mock()
        self.logger.warning = Mock()


class MockWorkflowContext:
    """Mock WorkflowContext for testing."""

    def __init__(self):
        self.data = {}
        self.metadata = {}
        self.errors = []

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data

    def add_metadata(self, metadata):
        self.metadata.update(metadata)

    def add_error(self, error):
        self.errors.append(error)


# Create mock modules
entity_core_plugin = type(sys)("entity.core.plugin")
entity_core_plugin.BasePlugin = MockBasePlugin

entity_workflow_context = type(sys)("entity.workflow.context")
entity_workflow_context.WorkflowContext = MockWorkflowContext

# Add to sys.modules
sys.modules["entity"] = Mock()
sys.modules["entity.core"] = Mock()
sys.modules["entity.core.plugin"] = entity_core_plugin
sys.modules["entity.workflow"] = Mock()
sys.modules["entity.workflow.context"] = entity_workflow_context


@pytest.fixture
def mock_logger():
    """Provide a mock logger for tests."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    return logger


@pytest.fixture
def sample_config():
    """Provide a sample configuration for tests."""
    return {"stage": "preprocessing", "option1": "test_value", "option2": False}


@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {
        "text": "Sample text for processing",
        "metadata": {"source": "test", "timestamp": "2024-01-01T12:00:00"},
    }
