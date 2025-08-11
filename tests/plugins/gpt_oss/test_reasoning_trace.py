"""Unit tests for ReasoningTracePlugin."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entity.plugins.context import PluginContext
from entity.plugins.gpt_oss import ReasoningLevel, ReasoningTrace, ReasoningTracePlugin
from entity.workflow.executor import WorkflowExecutor


class TestReasoningTracePlugin:
    """Test ReasoningTracePlugin functionality."""

    @pytest.fixture
    def mock_resources(self):
        """Create mock resources for testing."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="Test response")

        # Create an async mock for memory that properly handles store/load
        class MockMemory:
            def __init__(self):
                self.data = {}

            async def store(self, key, value):
                self.data[key] = value

            async def load(self, key, default=None):
                return self.data.get(key, default)

        return {
            "llm": mock_llm,
            "memory": MockMemory(),
        }

    @pytest.fixture
    def plugin(self, mock_resources):
        """Create a plugin instance for testing."""
        config = {
            "default_level": "medium",
            "enable_filtering": True,
            "store_commentary": True,
            "complexity_threshold_high": 0.8,
            "complexity_threshold_medium": 0.4,
        }
        return ReasoningTracePlugin(mock_resources, config)

    @pytest.fixture
    def context(self, mock_resources):
        """Create a mock plugin context."""
        ctx = PluginContext(mock_resources, "test_user")
        ctx.current_stage = WorkflowExecutor.THINK
        ctx.message = "Test task message"
        # Make get_resource return proper mocks
        ctx.get_resource = lambda name: mock_resources.get(name)
        return ctx

    def test_plugin_initialization(self, plugin):
        """Test that plugin initializes correctly."""
        assert plugin.config.default_level == "medium"  # ConfigModel stores as string
        assert plugin.config.enable_filtering is True
        assert plugin.config.store_commentary is True
        assert WorkflowExecutor.THINK in plugin.supported_stages
        assert "llm" in plugin.dependencies
        assert "memory" in plugin.dependencies

    def test_config_validation(self, mock_resources):
        """Test configuration validation."""
        # Valid config
        config = {"default_level": "high", "enable_filtering": False}
        plugin = ReasoningTracePlugin(mock_resources, config)
        assert plugin.config.default_level == "high"  # ConfigModel stores as string
        assert plugin.config.enable_filtering is False

        # Invalid reasoning level should fail
        with pytest.raises(Exception):
            ReasoningTracePlugin(mock_resources, {"default_level": "invalid"})

    @pytest.mark.asyncio
    async def test_calculate_complexity_simple(self, plugin):
        """Test complexity calculation for simple tasks."""
        simple_task = "What is 2 + 2?"
        score = await plugin._calculate_complexity(simple_task)
        assert score < 0.4  # Should be LOW complexity

    @pytest.mark.asyncio
    async def test_calculate_complexity_medium(self, plugin):
        """Test complexity calculation for medium tasks."""
        medium_task = (
            "Explain how async functions work in Python and provide an example"
        )
        score = await plugin._calculate_complexity(medium_task)
        assert 0.4 <= score < 0.8  # Should be MEDIUM complexity

    @pytest.mark.asyncio
    async def test_calculate_complexity_high(self, plugin):
        """Test complexity calculation for complex tasks."""
        complex_task = """
        Analyze and optimize this algorithm for better performance:
        ```python
        def complex_function(data):
            # Implementation here
            pass
        ```
        Then implement a distributed version using async patterns.
        Finally, evaluate the performance improvements.
        """
        score = await plugin._calculate_complexity(complex_task)
        assert score >= 0.8  # Should be HIGH complexity

    @pytest.mark.asyncio
    async def test_determine_reasoning_level(self, plugin, context):
        """Test reasoning level determination based on complexity."""
        # Low complexity
        context.recall = AsyncMock(return_value=None)  # No override
        level = await plugin._determine_reasoning_level(context, "Simple question")
        assert level == ReasoningLevel.LOW

        # High complexity
        complex_task = "Explain, analyze, compare and evaluate multiple machine learning algorithms then implement distributed async patterns"
        level = await plugin._determine_reasoning_level(context, complex_task)
        assert level == ReasoningLevel.HIGH

    @pytest.mark.asyncio
    async def test_determine_reasoning_level_with_override(self, plugin, context):
        """Test manual reasoning level override."""
        # Set manual override
        context.recall = AsyncMock(return_value="high")

        # Even with simple task, should use override
        level = await plugin._determine_reasoning_level(context, "Simple task")
        assert level == ReasoningLevel.HIGH

    @pytest.mark.asyncio
    async def test_extract_analysis_channel_with_markers(self, plugin):
        """Test extracting analysis from response with channel markers."""
        response = """<<ANALYSIS>>
        This is the analysis content.
        Multiple lines of reasoning.

        <<COMMENTARY>>
        Some commentary here.

        <<FINAL>>
        Final response to user."""

        analysis = await plugin._extract_analysis_channel(response)
        assert "This is the analysis content" in analysis
        assert "Multiple lines of reasoning" in analysis
        assert "commentary" not in analysis.lower()
        assert "final response" not in analysis.lower()

    @pytest.mark.asyncio
    async def test_extract_analysis_channel_without_markers(self, plugin):
        """Test extracting analysis from response without channel markers."""
        response = """Let me think about this problem.
        First, I need to consider the requirements.
        The problem is complex and requires careful analysis.
        Therefore, the solution would be to implement it step by step.

        Here's the answer: 42"""

        analysis = await plugin._extract_analysis_channel(response)
        assert "Let me think" in analysis
        assert "First, I need" in analysis
        assert "The problem is" in analysis
        assert "Therefore" in analysis

    @pytest.mark.asyncio
    async def test_filter_harmful_content(self, plugin):
        """Test harmful content filtering."""
        content = """Normal reasoning line.
        This contains an exploit attempt.
        Another normal line.
        Something about illegal activities.
        Final normal content."""

        clean, filtered = await plugin._filter_harmful_content(content)

        # Check filtered content
        assert "exploit" not in clean.lower()
        assert "illegal" not in clean.lower()
        assert "Normal reasoning line" in clean
        assert "Another normal line" in clean
        assert "Final normal content" in clean

        # Check filtered list
        assert len(filtered) == 2
        assert any("[FILTERED]" in f for f in filtered)

    @pytest.mark.asyncio
    async def test_execute_with_harmony_infrastructure(self, plugin, context):
        """Test execution with harmony infrastructure that has channels."""
        # Mock harmony infrastructure
        mock_infra = MagicMock()
        mock_infra.generate_with_channels = AsyncMock(
            return_value={
                "analysis": "Analysis content here",
                "commentary": "Commentary content",
                "final": "Final response",
            }
        )

        context.get_resource("llm").infrastructure = mock_infra
        context.remember = AsyncMock()
        context.recall = AsyncMock(return_value=[])

        with patch.object(plugin, "_calculate_complexity", return_value=0.5):
            result = await plugin._execute_impl(context)

        # Should pass through the message
        assert result == context.message

        # Should have stored reasoning trace
        context.remember.assert_called()
        calls = context.remember.call_args_list

        # Find the reasoning trace call
        trace_call = None
        for call in calls:
            if "reasoning_trace:" in str(call[0][0]):
                trace_call = call
                break

        assert trace_call is not None
        trace_data = trace_call[0][1]
        assert trace_data["task"] == "Test task message"
        assert trace_data["analysis"] == "Analysis content here"
        assert trace_data["commentary"] == "Commentary content"
        assert trace_data["level"] == "medium"

    @pytest.mark.asyncio
    async def test_execute_without_harmony_infrastructure(self, plugin, context):
        """Test execution with regular LLM (no channels)."""
        # Mock regular LLM response
        mock_response = """<<ANALYSIS>>
        Analyzing the task...
        <<FINAL>>
        Here's the response."""

        # Make sure llm has no infrastructure attribute
        mock_llm = context.get_resource("llm")
        if hasattr(mock_llm, "infrastructure"):
            delattr(mock_llm, "infrastructure")
        mock_llm.generate = AsyncMock(return_value=mock_response)

        context.remember = AsyncMock()
        context.recall = AsyncMock(return_value=[])

        with patch.object(plugin, "_calculate_complexity", return_value=0.3):
            result = await plugin._execute_impl(context)

        # Should pass through the message
        assert result == context.message

        # Should have stored reasoning trace with LOW level
        calls = context.remember.call_args_list
        trace_call = None
        for call in calls:
            if "reasoning_trace:" in str(call[0][0]):
                trace_call = call
                break

        assert trace_call is not None
        trace_data = trace_call[0][1]
        assert trace_data["level"] == "low"
        assert "Analyzing the task" in trace_data["analysis"]

    @pytest.mark.asyncio
    async def test_execute_updates_history(self, plugin, context):
        """Test that execution updates reasoning history."""
        mock_llm = context.get_resource("llm")
        if hasattr(mock_llm, "infrastructure"):
            delattr(mock_llm, "infrastructure")
        mock_llm.generate = AsyncMock(return_value="Response")

        context.remember = AsyncMock()
        context.recall = AsyncMock(return_value=[])  # Empty history

        await plugin._execute_impl(context)

        # Should update history
        history_calls = [
            call
            for call in context.remember.call_args_list
            if call[0][0] == "reasoning_history"
        ]

        assert len(history_calls) == 1
        history = history_calls[0][0][1]
        assert len(history) == 1
        assert "execution_id" in history[0]
        assert "timestamp" in history[0]
        assert "task_preview" in history[0]
        assert "level" in history[0]
        assert "complexity" in history[0]

    @pytest.mark.asyncio
    async def test_execute_limits_history_size(self, plugin, context):
        """Test that reasoning history is limited to 100 entries."""
        # Create existing history with 100 entries
        existing_history = [
            {"execution_id": str(i), "timestamp": datetime.now().isoformat()}
            for i in range(100)
        ]

        mock_llm = context.get_resource("llm")
        if hasattr(mock_llm, "infrastructure"):
            delattr(mock_llm, "infrastructure")
        mock_llm.generate = AsyncMock(return_value="Response")

        context.remember = AsyncMock()
        context.recall = AsyncMock(return_value=existing_history)

        await plugin._execute_impl(context)

        # Check history was trimmed
        history_calls = [
            call
            for call in context.remember.call_args_list
            if call[0][0] == "reasoning_history"
        ]

        assert len(history_calls) == 1
        updated_history = history_calls[0][0][1]
        assert len(updated_history) == 100  # Still 100, oldest was removed

    @pytest.mark.asyncio
    async def test_retrieve_reasoning_history(self, context):
        """Test retrieving reasoning history with filters."""
        # Create test history
        test_history = [
            {
                "execution_id": "1",
                "complexity": 0.3,
                "level": "low",
                "timestamp": "2024-01-01",
            },
            {
                "execution_id": "2",
                "complexity": 0.5,
                "level": "medium",
                "timestamp": "2024-01-02",
            },
            {
                "execution_id": "3",
                "complexity": 0.9,
                "level": "high",
                "timestamp": "2024-01-03",
            },
        ]

        context.recall = AsyncMock(return_value=test_history)

        # Test with no filters
        history = await ReasoningTracePlugin.retrieve_reasoning_history(
            context, limit=10
        )
        assert len(history) == 3

        # Test with complexity filter
        history = await ReasoningTracePlugin.retrieve_reasoning_history(
            context, limit=10, min_complexity=0.5
        )
        assert len(history) == 2
        assert all(h["complexity"] >= 0.5 for h in history)

        # Test with level filter
        history = await ReasoningTracePlugin.retrieve_reasoning_history(
            context, limit=10, level=ReasoningLevel.HIGH
        )
        assert len(history) == 1
        assert history[0]["level"] == "high"

    @pytest.mark.asyncio
    async def test_get_reasoning_trace(self, context):
        """Test retrieving a specific reasoning trace."""
        trace_data = {
            "execution_id": "test-123",
            "timestamp": datetime.now().isoformat(),
            "level": "medium",  # Store as string
            "task": "Test task",
            "analysis": "Test analysis",
            "commentary": None,
            "filtered_content": [],
            "complexity_score": 0.5,
            "tokens_used": 100,
        }

        context.recall = AsyncMock(return_value=trace_data)

        trace = await ReasoningTracePlugin.get_reasoning_trace(context, "test-123")

        assert trace is not None
        assert trace.execution_id == "test-123"
        assert trace.level == "medium"  # Now stored as string
        assert trace.task == "Test task"
        assert trace.analysis == "Test analysis"

        # Test not found
        context.recall = AsyncMock(return_value=None)
        trace = await ReasoningTracePlugin.get_reasoning_trace(context, "not-found")
        assert trace is None

    @pytest.mark.asyncio
    async def test_analyze_reasoning_patterns(self, context):
        """Test analyzing reasoning patterns."""
        # Create test history
        test_history = [
            {"complexity": 0.3, "level": "low"},
            {"complexity": 0.5, "level": "medium"},
            {"complexity": 0.9, "level": "high"},
            {"complexity": 0.7, "level": "medium"},
            {"complexity": 0.85, "level": "high"},
        ]

        context.recall = AsyncMock(return_value=test_history)

        analysis = await ReasoningTracePlugin.analyze_reasoning_patterns(context, 24)

        assert analysis["total_traces"] == 5
        assert 0.6 < analysis["avg_complexity"] < 0.7
        assert analysis["level_distribution"]["low"] == 1
        assert analysis["level_distribution"]["medium"] == 2
        assert analysis["level_distribution"]["high"] == 2
        assert len(analysis["high_complexity_tasks"]) == 2

        # Test with empty history
        context.recall = AsyncMock(return_value=[])
        analysis = await ReasoningTracePlugin.analyze_reasoning_patterns(context, 24)
        assert analysis["total_traces"] == 0
        assert analysis["avg_complexity"] == 0

    def test_reasoning_trace_model(self):
        """Test ReasoningTrace model validation."""
        # Valid trace
        trace = ReasoningTrace(
            execution_id="test-123",
            timestamp=datetime.now().isoformat(),
            level="medium",  # String now
            task="Test task",
            analysis="Analysis content",
            complexity_score=0.5,
        )

        assert trace.execution_id == "test-123"
        assert trace.level == "medium"
        assert trace.commentary is None
        assert trace.filtered_content == []

        # Test with all fields
        trace = ReasoningTrace(
            execution_id="test-456",
            timestamp=datetime.now().isoformat(),
            level="high",  # String now
            task="Complex task",
            analysis="Deep analysis",
            commentary="Additional commentary",
            filtered_content=["filtered line 1"],
            complexity_score=0.9,
            tokens_used=500,
        )

        assert trace.commentary == "Additional commentary"
        assert trace.filtered_content == ["filtered line 1"]
        assert trace.tokens_used == 500

    def test_reasoning_level_enum(self):
        """Test ReasoningLevel enum."""
        assert ReasoningLevel.LOW.value == "low"
        assert ReasoningLevel.MEDIUM.value == "medium"
        assert ReasoningLevel.HIGH.value == "high"

        # Test from string
        level = ReasoningLevel("low")
        assert level == ReasoningLevel.LOW

        level = ReasoningLevel("HIGH".lower())
        assert level == ReasoningLevel.HIGH
