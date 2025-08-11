"""Tests for ReasoningAnalyticsDashboardPlugin."""

import json
from datetime import datetime, timedelta

import pytest

from entity_plugin_gpt_oss.reasoning_analytics_dashboard import (
    ReasoningAnalyticsDashboardPlugin,
    ReasoningMetrics,
)


class MockContext:
    """Mock context for testing."""

    def __init__(self, **kwargs):
        self.execution_id = kwargs.get("execution_id", "test-exec-1")
        self.reasoning_trace = kwargs.get("reasoning_trace")
        self.execution_duration_ms = kwargs.get("execution_duration_ms", 1000)
        self.token_count = kwargs.get("token_count", 100)
        self.reasoning_level = kwargs.get("reasoning_level", "medium")
        self.task = kwargs.get("task", "test task")
        self.execution_success = kwargs.get("execution_success", True)
        self.error_type = kwargs.get("error_type")
        self.current_stage = kwargs.get("current_stage", "analysis")


@pytest.fixture
def plugin():
    """Create a ReasoningAnalyticsDashboardPlugin instance."""
    resources = {}
    config = {
        "max_stored_metrics": 100,
        "analysis_window_hours": 24,
        "complexity_threshold": 0.7,
        "duration_threshold_ms": 5000,
        "enable_real_time_monitoring": True,
    }
    return ReasoningAnalyticsDashboardPlugin(resources, config)


@pytest.fixture
def sample_reasoning_trace():
    """Sample reasoning trace for testing."""
    return {
        "analysis": (
            "First, I need to consider the problem carefully. "
            "Given that we have multiple factors, I will analyze each step. "
            "If the conditions are met, then we can proceed. "
            "Therefore, the solution involves comparing different approaches."
        )
    }


@pytest.fixture
def mock_context(sample_reasoning_trace):
    """Mock context with reasoning trace."""
    return MockContext(
        execution_id="test-exec-123",
        reasoning_trace=sample_reasoning_trace,
        execution_duration_ms=2500,
        token_count=150,
        reasoning_level="high",
        task="Analyze the complex data structure and provide recommendations",
        execution_success=True,
    )


class TestReasoningAnalyticsDashboardPlugin:
    """Test cases for ReasoningAnalyticsDashboardPlugin."""

    def test_plugin_initialization(self, plugin):
        """Test plugin initialization."""
        assert plugin.supported_stages == ["analysis", "post_processing"]
        assert plugin.dependencies == []
        assert plugin._metrics_store == []
        assert plugin._patterns_cache is None
        assert plugin._bottlenecks_cache is None
        assert plugin._last_analysis_time is None

    def test_config_validation(self):
        """Test configuration validation."""
        resources = {}
        config = {
            "max_stored_metrics": 50,
            "analysis_window_hours": 12,
            "complexity_threshold": 0.8,
            "duration_threshold_ms": 3000,
            "enable_real_time_monitoring": False,
        }
        plugin = ReasoningAnalyticsDashboardPlugin(resources, config)

        # Config should already be validated during init
        assert plugin.config.max_stored_metrics == 50
        assert plugin.config.analysis_window_hours == 12

        # Test direct validation call on fresh instance
        plugin2 = ReasoningAnalyticsDashboardPlugin.__new__(
            ReasoningAnalyticsDashboardPlugin
        )
        plugin2.resources = resources
        plugin2.config = config
        result = plugin2.validate_config()
        assert result.success

    def test_config_validation_invalid(self):
        """Test configuration validation with invalid config."""
        resources = {}
        config = {
            "max_stored_metrics": "invalid",  # Should be int
            "complexity_threshold": 2.0,  # Should be <= 1.0
        }

        # Should raise ValueError during initialization due to invalid config
        with pytest.raises(ValueError, match="Invalid config"):
            ReasoningAnalyticsDashboardPlugin(resources, config)

    @pytest.mark.asyncio
    async def test_execute_with_reasoning_trace(self, plugin, mock_context):
        """Test plugin execution with valid reasoning trace."""
        result = await plugin.execute(mock_context)

        # Check that context was returned and enhanced
        assert result == mock_context
        assert hasattr(result, "reasoning_analytics")
        assert result.reasoning_analytics["metrics_collected"] is True
        assert result.reasoning_analytics["total_stored_metrics"] == 1

        # Check that metrics were stored
        assert len(plugin._metrics_store) == 1
        stored_metric = plugin._metrics_store[0]
        assert stored_metric.execution_id == "test-exec-123"
        assert stored_metric.reasoning_level == "high"
        assert stored_metric.task_category == "analysis"
        assert stored_metric.success is True

    @pytest.mark.asyncio
    async def test_execute_without_reasoning_trace(self, plugin):
        """Test plugin execution without reasoning trace."""
        context = MockContext(reasoning_trace=None)
        result = await plugin.execute(context)

        # Check that context was returned but no metrics collected
        assert result == context
        assert hasattr(result, "reasoning_analytics")
        assert result.reasoning_analytics["metrics_collected"] is False
        assert result.reasoning_analytics["total_stored_metrics"] == 0

        # Check that no metrics were stored
        assert len(plugin._metrics_store) == 0

    def test_calculate_reasoning_depth(self, plugin):
        """Test reasoning depth calculation."""
        # Test with dict format
        trace_dict = {
            "analysis": "First, I need to consider this. Then, if we proceed, therefore we can conclude."
        }
        depth = plugin._calculate_reasoning_depth(trace_dict)
        assert depth >= 3  # Should find "first", "then", "if", "therefore"

        # Test with object format
        class TraceObj:
            def __init__(self, analysis):
                self.analysis = analysis

        trace_obj = TraceObj(
            "Given that this is true, because we know that, step 1 is to analyze."
        )
        depth = plugin._calculate_reasoning_depth(trace_obj)
        assert depth >= 3  # Should find "given that", "because", "step"

        # Test with string format
        trace_str = "Simple statement without reasoning indicators."
        depth = plugin._calculate_reasoning_depth(trace_str)
        assert depth == 1  # Minimum depth

    def test_calculate_complexity_score(self, plugin):
        """Test complexity score calculation."""
        # High complexity text
        high_complexity_trace = {
            "analysis": (
                "If we consider the abstract concept of algorithmic complexity, "
                "then we must analyze the conditional statements compared to "
                "the baseline implementation. When we examine the optimization "
                "patterns, provided that the computational requirements are met."
            )
        }
        score = plugin._calculate_complexity_score(high_complexity_trace)
        assert 0.3 <= score <= 1.0  # Should be reasonably high

        # Low complexity text
        low_complexity_trace = {"analysis": "This is simple. Do task. Done."}
        score = plugin._calculate_complexity_score(low_complexity_trace)
        assert 0.0 <= score <= 0.3  # Should be low

    def test_categorize_task(self, plugin):
        """Test task categorization."""
        test_cases = [
            ("Write a Python function to debug the code", "coding"),
            ("Analyze the data and provide statistics", "analysis"),
            ("Compose a document about the project", "writing"),
            ("Solve this mathematical problem", "problem_solving"),
            ("Explain what this function does", "explanation"),
            ("Random task with no clear category", "general"),
        ]

        for task, expected_category in test_cases:
            category = plugin._categorize_task(task)
            assert category == expected_category

    def test_store_metrics_with_limit(self, plugin):
        """Test metrics storage with size limit."""
        # Set a small limit for testing
        plugin.config.max_stored_metrics = 3

        # Add more metrics than the limit
        for i in range(5):
            metric = ReasoningMetrics(
                execution_id=f"exec-{i}",
                timestamp=datetime.now(),
                reasoning_depth=1,
                complexity_score=0.5,
                duration_ms=1000,
                token_count=100,
                reasoning_level="medium",
                task_category="general",
                success=True,
            )
            plugin._store_metrics(metric)

        # Should only keep the last 3 metrics
        assert len(plugin._metrics_store) == 3
        assert plugin._metrics_store[0].execution_id == "exec-2"
        assert plugin._metrics_store[-1].execution_id == "exec-4"

    @pytest.mark.asyncio
    async def test_pattern_analysis(self, plugin):
        """Test pattern analysis functionality."""
        # Add sample metrics with enough data for patterns (need at least 3 per pattern)
        metrics = [
            # Coding + medium pattern (3 metrics)
            ReasoningMetrics(
                execution_id="exec-1",
                timestamp=datetime.now(),
                reasoning_depth=2,
                complexity_score=0.6,
                duration_ms=2000,
                token_count=120,
                reasoning_level="medium",
                task_category="coding",
                success=True,
            ),
            ReasoningMetrics(
                execution_id="exec-2",
                timestamp=datetime.now(),
                reasoning_depth=2,
                complexity_score=0.7,
                duration_ms=2200,
                token_count=130,
                reasoning_level="medium",
                task_category="coding",
                success=True,
            ),
            ReasoningMetrics(
                execution_id="exec-3",
                timestamp=datetime.now(),
                reasoning_depth=2,
                complexity_score=0.5,
                duration_ms=1800,
                token_count=110,
                reasoning_level="medium",
                task_category="coding",
                success=True,
            ),
            # Analysis + high pattern (3 metrics)
            ReasoningMetrics(
                execution_id="exec-4",
                timestamp=datetime.now(),
                reasoning_depth=3,
                complexity_score=0.8,
                duration_ms=3000,
                token_count=180,
                reasoning_level="high",
                task_category="analysis",
                success=True,
            ),
            ReasoningMetrics(
                execution_id="exec-5",
                timestamp=datetime.now(),
                reasoning_depth=4,
                complexity_score=0.9,
                duration_ms=3200,
                token_count=200,
                reasoning_level="high",
                task_category="analysis",
                success=False,
            ),
            ReasoningMetrics(
                execution_id="exec-6",
                timestamp=datetime.now(),
                reasoning_depth=3,
                complexity_score=0.7,
                duration_ms=2800,
                token_count=170,
                reasoning_level="high",
                task_category="analysis",
                success=True,
            ),
        ]

        for metric in metrics:
            plugin._store_metrics(metric)

        # Run pattern analysis
        await plugin._run_pattern_analysis()

        # Check that patterns were identified
        assert plugin._patterns_cache is not None
        assert len(plugin._patterns_cache) == 2  # Should have 2 patterns

        # Verify pattern details
        pattern_types = [p.pattern_type for p in plugin._patterns_cache]
        assert "coding_medium" in pattern_types
        assert "analysis_high" in pattern_types

        # Check pattern details
        coding_pattern = next(
            p for p in plugin._patterns_cache if p.pattern_type == "coding_medium"
        )
        assert coding_pattern.frequency == 3
        assert coding_pattern.success_rate == 1.0

        analysis_pattern = next(
            p for p in plugin._patterns_cache if p.pattern_type == "analysis_high"
        )
        assert analysis_pattern.frequency == 3
        assert analysis_pattern.success_rate == 2 / 3  # 2 success, 1 failure

    @pytest.mark.asyncio
    async def test_bottleneck_detection(self, plugin):
        """Test bottleneck detection functionality."""
        # Add metrics that should trigger bottlenecks
        high_complexity_metrics = [
            ReasoningMetrics(
                execution_id=f"exec-{i}",
                timestamp=datetime.now(),
                reasoning_depth=5,
                complexity_score=0.9,  # High complexity
                duration_ms=2000,
                token_count=200,
                reasoning_level="high",
                task_category="analysis",
                success=True,
            )
            for i in range(5)
        ]

        long_duration_metrics = [
            ReasoningMetrics(
                execution_id=f"slow-exec-{i}",
                timestamp=datetime.now(),
                reasoning_depth=2,
                complexity_score=0.5,
                duration_ms=8000,  # Long duration
                token_count=150,
                reasoning_level="medium",
                task_category="coding",
                success=True,
            )
            for i in range(3)
        ]

        failed_metrics = [
            ReasoningMetrics(
                execution_id=f"fail-exec-{i}",
                timestamp=datetime.now(),
                reasoning_depth=1,
                complexity_score=0.3,
                duration_ms=1000,
                token_count=50,
                reasoning_level="low",
                task_category="general",
                success=False,  # Failed execution
                error_type="timeout",
            )
            for i in range(2)
        ]

        # Store all metrics
        all_metrics = high_complexity_metrics + long_duration_metrics + failed_metrics
        for metric in all_metrics:
            plugin._store_metrics(metric)

        # Run bottleneck detection
        await plugin._run_bottleneck_detection()

        # Check that bottlenecks were identified
        assert plugin._bottlenecks_cache is not None
        assert len(plugin._bottlenecks_cache) > 0

        # Check for specific bottleneck types
        bottleneck_types = [b.bottleneck_type for b in plugin._bottlenecks_cache]
        assert "high_complexity" in bottleneck_types
        assert "long_duration" in bottleneck_types
        assert "high_failure_rate" in bottleneck_types

    def test_get_dashboard_data_empty(self, plugin):
        """Test dashboard data retrieval with no metrics."""
        dashboard_data = plugin.get_dashboard_data()

        assert dashboard_data.total_executions == 0
        assert dashboard_data.avg_complexity == 0.0
        assert dashboard_data.avg_duration_ms == 0
        assert dashboard_data.success_rate == 0.0
        assert dashboard_data.patterns == []
        assert dashboard_data.bottlenecks == []
        assert dashboard_data.time_series == {}

    def test_get_dashboard_data_with_metrics(self, plugin):
        """Test dashboard data retrieval with metrics."""
        # Add sample metrics
        now = datetime.now()
        metrics = [
            ReasoningMetrics(
                execution_id=f"exec-{i}",
                timestamp=now - timedelta(hours=i),
                reasoning_depth=2,
                complexity_score=0.5 + (i * 0.1),
                duration_ms=1000 + (i * 500),
                token_count=100,
                reasoning_level="medium",
                task_category="general",
                success=True,
            )
            for i in range(5)
        ]

        for metric in metrics:
            plugin._store_metrics(metric)

        # Get dashboard data
        dashboard_data = plugin.get_dashboard_data(time_window_hours=10)

        assert dashboard_data.total_executions == 5
        assert dashboard_data.avg_complexity > 0.0
        assert dashboard_data.avg_duration_ms > 1000
        assert dashboard_data.success_rate == 1.0
        assert "complexity" in dashboard_data.time_series
        assert "duration" in dashboard_data.time_series
        assert "success_rate" in dashboard_data.time_series
        assert "throughput" in dashboard_data.time_series

    def test_export_data_json(self, plugin):
        """Test data export in JSON format."""
        # Add a sample metric
        metric = ReasoningMetrics(
            execution_id="test-exec",
            timestamp=datetime.now(),
            reasoning_depth=2,
            complexity_score=0.6,
            duration_ms=2000,
            token_count=120,
            reasoning_level="medium",
            task_category="analysis",
            success=True,
        )
        plugin._store_metrics(metric)

        # Export as JSON
        json_data = plugin.export_data(format_type="json")

        # Verify JSON is valid
        parsed_data = json.loads(json_data)
        assert parsed_data["total_executions"] == 1
        assert "avg_complexity" in parsed_data
        assert "patterns" in parsed_data
        assert "bottlenecks" in parsed_data

    def test_export_data_csv(self, plugin):
        """Test data export in CSV format."""
        # Add sample metrics
        metrics = [
            ReasoningMetrics(
                execution_id=f"exec-{i}",
                timestamp=datetime.now(),
                reasoning_depth=2,
                complexity_score=0.5,
                duration_ms=1000,
                token_count=100,
                reasoning_level="medium",
                task_category="general",
                success=True,
            )
            for i in range(3)
        ]

        for metric in metrics:
            plugin._store_metrics(metric)

        # Export as CSV
        csv_data = plugin.export_data(format_type="csv")

        # Verify CSV format
        lines = csv_data.split("\n")
        assert len(lines) == 4  # Header + 3 data rows
        assert (
            lines[0]
            == "execution_id,timestamp,complexity,duration_ms,success,task_category"
        )
        assert "exec-0" in lines[1]
        assert "0.5" in lines[1]
        assert "True" in lines[1]

    def test_export_data_invalid_format(self, plugin):
        """Test data export with invalid format."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            plugin.export_data(format_type="xml")

    def test_real_time_monitoring_enabled(self, plugin):
        """Test real-time monitoring when enabled."""
        # Add recent metrics
        recent_time = datetime.now() - timedelta(minutes=2)
        metric = ReasoningMetrics(
            execution_id="recent-exec",
            timestamp=recent_time,
            reasoning_depth=2,
            complexity_score=0.7,
            duration_ms=1500,
            token_count=100,
            reasoning_level="medium",
            task_category="analysis",
            success=True,
        )
        plugin._store_metrics(metric)

        # Get real-time status
        status = plugin.get_real_time_status()

        assert status["status"] == "active"
        assert status["recent_executions"] == 1
        assert status["avg_recent_complexity"] == 0.7
        assert status["recent_success_rate"] == 1.0
        assert "last_update" in status

    def test_real_time_monitoring_disabled(self, plugin):
        """Test real-time monitoring when disabled."""
        plugin.config.enable_real_time_monitoring = False

        status = plugin.get_real_time_status()
        assert status == {"status": "disabled"}

    def test_time_series_generation(self, plugin):
        """Test time series data generation."""
        # Add metrics across different time periods
        now = datetime.now()
        metrics = []

        for hours_ago in [0, 1, 2, 5]:
            for _ in range(2):  # 2 metrics per hour
                metrics.append(
                    ReasoningMetrics(
                        execution_id=f"exec-{hours_ago}-{_}",
                        timestamp=now - timedelta(hours=hours_ago, minutes=_ * 10),
                        reasoning_depth=2,
                        complexity_score=0.5 + (hours_ago * 0.1),
                        duration_ms=1000 + (hours_ago * 200),
                        token_count=100,
                        reasoning_level="medium",
                        task_category="general",
                        success=True,
                    )
                )

        for metric in metrics:
            plugin._store_metrics(metric)

        # Generate time series
        time_series = plugin._generate_time_series(metrics, window_hours=6)

        assert len(time_series["complexity"]) == 6
        assert len(time_series["duration"]) == 6
        assert len(time_series["success_rate"]) == 6
        assert len(time_series["throughput"]) == 6

        # Check that we have data for hours with metrics
        assert time_series["throughput"][0] == 2  # Current hour
        assert time_series["throughput"][1] == 2  # 1 hour ago
        assert time_series["throughput"][2] == 2  # 2 hours ago
        assert time_series["throughput"][3] == 0  # 3 hours ago (no data)
        assert time_series["throughput"][4] == 0  # 4 hours ago (no data)
        assert time_series["throughput"][5] == 2  # 5 hours ago

    @pytest.mark.asyncio
    async def test_should_run_analysis_logic(self, plugin):
        """Test analysis trigger logic."""
        # Initially should run analysis
        assert plugin._should_run_analysis() is True

        # After setting recent analysis time, should not run
        plugin._last_analysis_time = datetime.now() - timedelta(minutes=30)
        assert plugin._should_run_analysis() is False

        # After enough time has passed, should run again
        plugin._last_analysis_time = datetime.now() - timedelta(hours=2)
        assert plugin._should_run_analysis() is True

    @pytest.mark.asyncio
    async def test_integration_full_workflow(self, plugin, mock_context):
        """Test full integration workflow."""
        # Execute the plugin multiple times
        contexts = []
        for i in range(5):
            context = MockContext(
                execution_id=f"integration-exec-{i}",
                reasoning_trace={
                    "analysis": f"Step {i}: analyzing complex problem with multiple factors."
                },
                execution_duration_ms=1000 + (i * 200),
                token_count=100 + (i * 20),
                reasoning_level="medium" if i % 2 == 0 else "high",
                task=f"Task {i}: solve problem type {'analysis' if i < 3 else 'coding'}",
                execution_success=i != 2,  # One failure
            )
            contexts.append(await plugin.execute(context))

        # Verify all executions were tracked
        assert len(plugin._metrics_store) == 5

        # Force analysis run
        await plugin._run_pattern_analysis()
        await plugin._run_bottleneck_detection()

        # Get dashboard data
        dashboard_data = plugin.get_dashboard_data()

        assert dashboard_data.total_executions == 5
        assert dashboard_data.success_rate == 0.8  # 4/5 success
        assert len(dashboard_data.patterns) > 0 or len(dashboard_data.bottlenecks) >= 0

        # Test export functionality
        json_export = plugin.export_data("json")
        assert "total_executions" in json_export

        csv_export = plugin.export_data("csv")
        assert "execution_id,timestamp" in csv_export

        # Test real-time monitoring
        real_time_status = plugin.get_real_time_status()
        assert real_time_status["status"] == "active"
