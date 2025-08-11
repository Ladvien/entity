"""
Test configuration and fixtures for GPT-OSS plugins.
"""

import sys
from unittest.mock import Mock, MagicMock
import pytest


# Mock the entity-core imports for testing
class MockPlugin:
    """Mock Plugin base class for testing."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = Mock()
        self.logger.info = Mock()
        self.logger.error = Mock()
        self.logger.warning = Mock()


class MockPromptPlugin(MockPlugin):
    """Mock PromptPlugin for testing."""
    pass


class MockPluginContext:
    """Mock PluginContext for testing."""
    
    def __init__(self):
        self.data = {}
        self.metadata = {}
        self.errors = []
        self.plugins = []
    
    def get_data(self):
        return self.data
    
    def set_data(self, data):
        self.data = data
    
    def add_metadata(self, metadata):
        self.metadata.update(metadata)
    
    def add_error(self, error):
        self.errors.append(error)
        
    def say(self, message):
        """Mock context.say method."""
        pass


class MockWorkflowExecutor:
    """Mock WorkflowExecutor for testing."""
    
    # Stage constants for backward compatibility
    INPUT = "INPUT"
    PARSE = "PARSE"
    THINK = "THINK"
    DO = "DO"
    REVIEW = "REVIEW"
    OUTPUT = "OUTPUT"
    ERROR = "ERROR"
    
    def __init__(self):
        self.plugins = []
        self.context = MockPluginContext()
    
    def add_plugin(self, plugin, stage=None):
        self.plugins.append((plugin, stage))
    
    async def run(self, data):
        return self.context


# Create mock modules - only if they don't already exist
if 'entity' not in sys.modules:
    entity_plugins_base = type(sys)('entity.plugins.base')
    entity_plugins_base.Plugin = MockPlugin
    
    entity_plugins_prompt = type(sys)('entity.plugins.prompt')
    entity_plugins_prompt.PromptPlugin = MockPromptPlugin
    
    entity_plugins_context = type(sys)('entity.plugins.context')
    entity_plugins_context.PluginContext = MockPluginContext
    
    entity_workflow_executor = type(sys)('entity.workflow.executor')
    entity_workflow_executor.WorkflowExecutor = MockWorkflowExecutor
    
    # Add to sys.modules
    sys.modules['entity'] = Mock()
    sys.modules['entity.plugins'] = Mock()
    sys.modules['entity.plugins.base'] = entity_plugins_base
    sys.modules['entity.plugins.prompt'] = entity_plugins_prompt
    sys.modules['entity.plugins.context'] = entity_plugins_context
    sys.modules['entity.workflow'] = Mock()
    sys.modules['entity.workflow.executor'] = entity_workflow_executor


@pytest.fixture
def mock_plugin_context():
    """Provide a mock plugin context for tests."""
    return MockPluginContext()


@pytest.fixture
def mock_workflow_executor():
    """Provide a mock workflow executor for tests."""
    return MockWorkflowExecutor()


@pytest.fixture
def sample_gpt_oss_response():
    """Provide sample GPT-OSS response for testing."""
    return {
        "choices": [{
            "message": {
                "content": "Sample response content",
                "reasoning": "Sample reasoning trace",
                "tool_calls": []
            }
        }],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
    }


@pytest.fixture
def sample_config():
    """Provide sample plugin configuration."""
    return {
        "enabled": True,
        "debug_mode": False,
        "rate_limit": "10/minute",
        "safety_level": "moderate"
    }