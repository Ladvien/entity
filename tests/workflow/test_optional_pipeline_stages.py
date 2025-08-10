"""Tests for optional pipeline stages (Story 14)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext
from entity.workflow.executor import WorkflowExecutor
from entity.workflow.pipeline_analyzer import PipelineAnalyzer
from entity.workflow.workflow import Workflow


class AlwaysRunPlugin(Plugin):
    """Plugin that always executes."""

    supported_stages = [WorkflowExecutor.PARSE]

    async def _execute_impl(self, context):
        return context.message + " [always]"


class ConditionalPlugin(Plugin):
    """Plugin with skip conditions."""

    supported_stages = [WorkflowExecutor.PARSE]
    skip_conditions = [
        lambda ctx: len(ctx.message) < 10,
        lambda ctx: ctx.user_id == "skip_user",
    ]

    async def _execute_impl(self, context):
        return context.message + " [conditional]"


class CustomSkipPlugin(Plugin):
    """Plugin with custom should_execute logic."""

    supported_stages = [WorkflowExecutor.THINK]

    def __init__(self, resources, config=None):
        super().__init__(resources, config)
        self.execute_count = 0
        self.skip_count = 0

    def should_execute(self, context):
        # Skip if message contains "skip"
        if "skip" in context.message.lower():
            self.skip_count += 1
            return False

        # Check parent conditions
        if not super().should_execute(context):
            self.skip_count += 1
            return False

        return True

    async def _execute_impl(self, context):
        self.execute_count += 1
        return context.message + " [custom]"


class DependentPlugin(Plugin):
    """Plugin that depends on previous stages."""

    supported_stages = [WorkflowExecutor.DO]

    def should_execute(self, context):
        # Skip if PARSE stage was skipped
        if WorkflowExecutor.PARSE in context.skipped_stages:
            return False
        return super().should_execute(context)

    async def _execute_impl(self, context):
        return context.message + " [dependent]"


class TestPluginSkipping:
    """Test plugin-level skipping functionality."""

    @pytest.fixture
    def resources(self):
        """Create mock resources."""
        resources = {
            "memory": MagicMock(),
            "logging": MagicMock(),
        }
        resources["logging"].log = AsyncMock()
        return resources

    @pytest.fixture
    def context(self, resources):
        """Create a plugin context."""
        ctx = PluginContext(resources, "test_user")
        ctx.message = "Test message for processing"
        ctx.current_stage = WorkflowExecutor.PARSE
        ctx.log = AsyncMock()
        return ctx

    def test_always_run_plugin(self, resources, context):
        """Test plugin without skip conditions always executes."""
        plugin = AlwaysRunPlugin(resources)

        assert plugin.should_execute(context) is True

        # Even with empty message
        context.message = ""
        assert plugin.should_execute(context) is True

    def test_skip_conditions_short_message(self, resources, context):
        """Test skip condition for short messages."""
        plugin = ConditionalPlugin(resources)

        # Long message should execute
        context.message = "This is a long message"
        assert plugin.should_execute(context) is True

        # Short message should skip
        context.message = "Short"
        assert plugin.should_execute(context) is False

    def test_skip_conditions_user_filter(self, resources, context):
        """Test skip condition for specific users."""
        plugin = ConditionalPlugin(resources)

        # Normal user should execute
        context.user_id = "normal_user"
        assert plugin.should_execute(context) is True

        # Skip user should skip
        context.user_id = "skip_user"
        assert plugin.should_execute(context) is False

    def test_skip_conditions_multiple(self, resources, context):
        """Test multiple skip conditions (OR logic)."""
        plugin = ConditionalPlugin(resources)

        # Both conditions false - should execute
        context.message = "Long enough message"
        context.user_id = "normal_user"
        assert plugin.should_execute(context) is True

        # First condition true - should skip
        context.message = "Short"
        context.user_id = "normal_user"
        assert plugin.should_execute(context) is False

        # Second condition true - should skip
        context.message = "Long enough message"
        context.user_id = "skip_user"
        assert plugin.should_execute(context) is False

        # Both conditions true - should skip
        context.message = "Short"
        context.user_id = "skip_user"
        assert plugin.should_execute(context) is False

    def test_custom_should_execute(self, resources, context):
        """Test plugin with custom should_execute logic."""
        plugin = CustomSkipPlugin(resources)

        # Normal message should execute
        context.message = "Process this message"
        assert plugin.should_execute(context) is True

        # Message with "skip" should skip
        context.message = "Please skip this one"
        assert plugin.should_execute(context) is False
        assert plugin.skip_count == 1

        # Case insensitive
        context.message = "SKIP THIS TOO"
        assert plugin.should_execute(context) is False
        assert plugin.skip_count == 2

    @pytest.mark.asyncio
    async def test_dependent_plugin_skips(self, resources, context):
        """Test plugin that depends on previous stages."""
        plugin = DependentPlugin(resources)

        # Should execute when PARSE not skipped
        context.skipped_stages = []
        assert plugin.should_execute(context) is True

        # Should skip when PARSE was skipped
        context.skipped_stages = [WorkflowExecutor.PARSE]
        assert plugin.should_execute(context) is False


class TestStageSkipping:
    """Test stage-level skipping functionality."""

    @pytest.fixture
    def resources(self):
        """Create mock resources with logging."""
        resources = {
            "memory": MagicMock(),
            "logging": MagicMock(),
        }
        resources["memory"].store = AsyncMock()
        resources["memory"].load = AsyncMock(return_value=None)
        resources["logging"].log = AsyncMock()
        return resources

    @pytest.fixture
    def workflow(self):
        """Create a workflow."""
        return Workflow(steps={}, supported_stages=list(WorkflowExecutor._ORDER))

    @pytest.fixture
    def executor(self, resources, workflow):
        """Create a workflow executor."""
        return WorkflowExecutor(resources, workflow)

    @pytest.mark.asyncio
    async def test_stage_skipped_when_no_plugins(self, resources, workflow, executor):
        """Test stage is skipped when no plugins will execute."""
        # Add plugin that will skip
        plugin = ConditionalPlugin(resources)
        workflow.steps[WorkflowExecutor.PARSE] = [plugin]

        # Execute with conditions that cause skip
        await executor.execute("Short", "skip_user")

        # Check metrics
        metrics = executor.get_skip_metrics()
        assert metrics["plugins_skipped"] > 0
        assert metrics["stages_skipped"] > 0

    @pytest.mark.asyncio
    async def test_stage_not_skipped_with_active_plugins(
        self, resources, workflow, executor
    ):
        """Test stage runs when at least one plugin is active."""
        # Add two plugins - one skips, one runs
        skip_plugin = ConditionalPlugin(resources)
        run_plugin = AlwaysRunPlugin(resources)

        workflow.steps[WorkflowExecutor.PARSE] = [skip_plugin, run_plugin]

        # Execute with conditions that cause first plugin to skip
        result = await executor.execute("Short", "normal_user")

        # Check metrics
        metrics = executor.get_skip_metrics()
        assert metrics["plugins_skipped"] == 1  # ConditionalPlugin skipped
        assert metrics["total_plugins_run"] >= 1  # AlwaysRunPlugin ran
        assert "[always]" in result  # AlwaysRunPlugin modified message

    def test_can_skip_stage_dependencies(self, executor):
        """Test stage dependency checking."""
        context = MagicMock()
        context.skipped_stages = []

        # INPUT can't be skipped (it's first)
        assert executor._can_skip_stage(WorkflowExecutor.INPUT, context) is False

        # OUTPUT can't be skipped (it's required)
        assert executor._can_skip_stage(WorkflowExecutor.OUTPUT, context) is False

        # ERROR can't be skipped (it's required)
        assert executor._can_skip_stage(WorkflowExecutor.ERROR, context) is False

        # PARSE can be skipped if INPUT wasn't skipped
        assert executor._can_skip_stage(WorkflowExecutor.PARSE, context) is True

        # THINK can be skipped if dependencies not skipped
        assert executor._can_skip_stage(WorkflowExecutor.THINK, context) is True

        # But not if PARSE was skipped (it's a dependency)
        context.skipped_stages = [WorkflowExecutor.PARSE]
        assert executor._can_skip_stage(WorkflowExecutor.THINK, context) is False

    @pytest.mark.asyncio
    async def test_skipped_stages_tracked_in_context(
        self, resources, workflow, executor
    ):
        """Test that skipped stages are tracked in context."""
        # No plugins in THINK stage - should skip
        workflow.steps[WorkflowExecutor.PARSE] = [AlwaysRunPlugin(resources)]

        await executor.execute("Test message", "test_user")

        # Can't directly access context after execution, check via metrics
        metrics = executor.get_skip_metrics()
        # THINK, DO, REVIEW stages should be skipped (no plugins)
        assert metrics["stages_skipped"] >= 1


class TestPipelineAnalyzer:
    """Test pipeline analyzer functionality."""

    @pytest.fixture
    def resources(self):
        """Create mock resources."""
        return {
            "memory": MagicMock(),
            "logging": MagicMock(),
        }

    @pytest.fixture
    def workflow(self, resources):
        """Create workflow with various plugins."""
        wf = Workflow(steps={}, supported_stages=list(WorkflowExecutor._ORDER))
        wf.steps[WorkflowExecutor.PARSE] = [
            AlwaysRunPlugin(resources),
            ConditionalPlugin(resources),
        ]
        wf.steps[WorkflowExecutor.THINK] = [CustomSkipPlugin(resources)]
        wf.steps[WorkflowExecutor.DO] = [DependentPlugin(resources)]
        return wf

    @pytest.fixture
    def executor(self, resources, workflow):
        """Create executor."""
        return WorkflowExecutor(resources, workflow)

    @pytest.fixture
    def analyzer(self, workflow, executor):
        """Create pipeline analyzer."""
        return PipelineAnalyzer(workflow, executor)

    def test_analyze_without_context(self, analyzer):
        """Test static analysis without context."""
        result = analyzer.analyze()

        assert result.total_stages == 6  # All standard stages
        assert result.total_plugins == 4  # Four plugins added
        assert len(result.stage_dependencies) > 0
        assert len(result.optimization_hints) > 0

    def test_analyze_with_skip_context(self, analyzer, resources):
        """Test analysis with context that causes skips."""
        context = PluginContext(resources, "skip_user")
        context.message = "Short"

        result = analyzer.analyze(context)

        # ConditionalPlugin should be marked as skippable
        assert len(result.skippable_plugins) >= 1
        assert any("ConditionalPlugin" in p for p in result.skippable_plugins)

    def test_optimization_hints_generation(self, analyzer, resources):
        """Test generation of optimization hints."""
        context = PluginContext(resources, "normal_user")
        context.message = "skip this message"

        result = analyzer.analyze(context)

        # Should have hints
        assert len(result.optimization_hints) > 0

        # Check hint types
        hint_types = {hint.hint_type for hint in result.optimization_hints}
        assert "cache" in hint_types or "parallel" in hint_types or "skip" in hint_types

    def test_stage_skip_recommendations(self, analyzer, resources):
        """Test stage skip recommendations."""
        context = PluginContext(resources, "test_user")
        context.message = "Process this"
        context.skipped_stages = []

        recommendations = analyzer.get_stage_skip_recommendations(context)

        # Should have recommendations for all stages including ERROR
        assert len(recommendations) == 7  # 6 regular stages + ERROR

        # OUTPUT and ERROR should never be recommended to skip
        assert recommendations[WorkflowExecutor.OUTPUT] is False
        assert recommendations[WorkflowExecutor.ERROR] is False

    def test_validate_skip_conditions(self, analyzer, resources):
        """Test validation of plugin skip conditions."""
        # Plugin with proper skip conditions
        good_plugin = ConditionalPlugin(resources)
        warnings = analyzer.validate_skip_conditions(good_plugin)
        assert len(warnings) == 0

        # Plugin without skip conditions
        no_skip_plugin = AlwaysRunPlugin(resources)
        warnings = analyzer.validate_skip_conditions(no_skip_plugin)
        assert len(warnings) > 0
        assert any("empty skip_conditions" in w for w in warnings)

        # Plugin with custom should_execute
        custom_plugin = CustomSkipPlugin(resources)
        warnings = analyzer.validate_skip_conditions(custom_plugin)
        assert any(
            "overrides should_execute" in w or "no skip_conditions" in w
            for w in warnings
        )

    def test_estimated_savings(self, analyzer, resources):
        """Test estimated time savings calculation."""
        context = PluginContext(resources, "skip_user")
        context.message = "Short"

        result = analyzer.analyze(context)

        # Should have positive savings when plugins/stages skip
        if result.skippable_plugins or result.skippable_stages:
            assert result.estimated_savings_ms > 0


class TestMetrics:
    """Test skip metrics tracking."""

    @pytest.fixture
    def executor(self):
        """Create executor with minimal setup."""
        resources = {
            "memory": MagicMock(),
            "logging": MagicMock(),
        }
        resources["memory"].store = AsyncMock()
        resources["memory"].load = AsyncMock(return_value=None)
        resources["logging"].log = AsyncMock()
        workflow = Workflow(steps={}, supported_stages=list(WorkflowExecutor._ORDER))
        return WorkflowExecutor(resources, workflow)

    def test_initial_metrics(self, executor):
        """Test initial metric values."""
        metrics = executor.get_skip_metrics()

        assert metrics["stages_skipped"] == 0
        assert metrics["plugins_skipped"] == 0
        assert metrics["total_stages_run"] == 0
        assert metrics["total_plugins_run"] == 0

    def test_reset_metrics(self, executor):
        """Test resetting metrics."""
        # Modify metrics
        executor._skip_metrics["stages_skipped"] = 5
        executor._skip_metrics["plugins_skipped"] = 10

        # Reset
        executor.reset_skip_metrics()

        # Check reset
        metrics = executor.get_skip_metrics()
        assert metrics["stages_skipped"] == 0
        assert metrics["plugins_skipped"] == 0

    def test_metrics_are_copied(self, executor):
        """Test that get_skip_metrics returns a copy."""
        metrics1 = executor.get_skip_metrics()
        metrics1["stages_skipped"] = 100

        metrics2 = executor.get_skip_metrics()
        assert metrics2["stages_skipped"] == 0  # Original unchanged


class TestIntegration:
    """Integration tests for the complete skip system."""

    @pytest.fixture
    def full_workflow(self):
        """Create a complete workflow with multiple plugins."""
        resources = {
            "memory": MagicMock(),
            "logging": MagicMock(),
        }
        resources["memory"].store = AsyncMock()
        resources["memory"].load = AsyncMock(return_value=None)
        resources["logging"].log = AsyncMock()

        workflow = Workflow(steps={}, supported_stages=list(WorkflowExecutor._ORDER))
        executor = WorkflowExecutor(resources, workflow)

        # Add plugins to different stages
        workflow.steps[WorkflowExecutor.PARSE] = [ConditionalPlugin(resources)]
        workflow.steps[WorkflowExecutor.THINK] = [CustomSkipPlugin(resources)]
        workflow.steps[WorkflowExecutor.DO] = [DependentPlugin(resources)]

        return workflow, executor, resources

    @pytest.mark.asyncio
    async def test_full_pipeline_with_skips(self, full_workflow):
        """Test complete pipeline execution with various skips."""
        workflow, executor, resources = full_workflow

        # Execute with message that causes THINK to skip
        result = await executor.execute("skip thinking please", "test_user")

        # Get metrics
        metrics = executor.get_skip_metrics()

        # CustomSkipPlugin should have skipped
        assert metrics["plugins_skipped"] >= 1

        # But pipeline should complete
        assert result is not None

    @pytest.mark.asyncio
    async def test_analyzer_with_real_execution(self, full_workflow):
        """Test analyzer with real execution data."""
        workflow, executor, resources = full_workflow

        # Create analyzer
        analyzer = PipelineAnalyzer(workflow, executor)

        # Analyze before execution
        static_analysis = analyzer.analyze()
        assert static_analysis.total_plugins == 3

        # Execute
        await executor.execute("Process this message", "test_user")

        # Analyze with context
        context = PluginContext(resources, "skip_user")
        context.message = "Short"
        runtime_analysis = analyzer.analyze(context)

        # Should identify skippable plugins
        assert len(runtime_analysis.skippable_plugins) >= 1

    @pytest.mark.asyncio
    async def test_cascading_skips(self, full_workflow):
        """Test that skipping stages affects dependent plugins."""
        workflow, executor, resources = full_workflow

        # Execute with very short message that causes PARSE to skip
        # Since all PARSE plugins skip, stage should skip
        # This should cause DependentPlugin to skip too
        await executor.execute("Hi", "skip_user")

        metrics = executor.get_skip_metrics()

        # Multiple plugins should skip due to cascading
        assert metrics["plugins_skipped"] >= 2
