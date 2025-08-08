"""Test Agent functionality with mocked infrastructure."""

from unittest.mock import Mock

import pytest

from entity.core.agent import Agent
from entity.resources.file_storage_wrapper import FileStorage
from entity.resources.llm import LLMResource
from entity.resources.logging import RichLoggingResource
from entity.resources.memory import Memory


def test_agent_initialization_with_resources():
    """Test Agent can be initialized with custom resources."""
    mock_llm = Mock(spec=LLMResource)
    mock_memory = Mock(spec=Memory)
    mock_storage = Mock(spec=FileStorage)
    mock_logging = Mock(spec=RichLoggingResource)

    resources = {
        "llm": mock_llm,
        "memory": mock_memory,
        "file_storage": mock_storage,
        "logging": mock_logging,
    }

    agent = Agent(resources=resources)

    assert agent.resources == resources
    assert agent.workflow is None
    assert agent.infrastructure is None


def test_agent_clear_config_cache():
    """Test cache clearing functionality."""
    # Add something to cache first
    Agent._config_cache["test"] = Mock()
    assert len(Agent._config_cache) > 0

    # Clear cache
    Agent.clear_from_config_cache()

    assert len(Agent._config_cache) == 0


def test_agent_initialization_validation():
    """Test Agent validates resources parameter."""
    with pytest.raises(TypeError, match="resources must be a mapping"):
        Agent(resources="not_a_dict")
