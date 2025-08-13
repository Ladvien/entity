"""Tests for architectural pattern examples."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from entity.workflow.stages import DO, INPUT, OUTPUT, PARSE, REVIEW, THINK

# Import the pattern plugins
from plugins.examples.src.entity_plugin_examples.patterns import (
    ConstructorInjectionPlugin,
    DualInterfacePlugin,
    EnvironmentSubstitutionPlugin,
    MultiStageAnalyticsPlugin,
)
from plugins.examples.src.entity_plugin_examples.patterns.constructor_injection import (
    CacheService,
    DatabaseService,
)


class TestConstructorInjectionPlugin:
    """Test constructor injection pattern."""

    @pytest.mark.asyncio
    async def test_constructor_injection_with_mocked_services(self):
        """Test plugin with injected mock services."""
        # Create mock services
        mock_db = Mock(spec=DatabaseService)
        mock_db.query = AsyncMock(
            return_value={"result": "test_data", "connection": "mock_db"}
        )

        mock_cache = Mock(spec=CacheService)
        mock_cache.get = AsyncMock(return_value=None)  # Cache miss
        mock_cache.set = AsyncMock()

        # Inject mocks via constructor
        plugin = ConstructorInjectionPlugin(
            resources={},
            config={"database_service": mock_db, "cache_service": mock_cache},
        )

        # Create mock context
        context = Mock()
        context.message = "test message"

        # Execute plugin
        result = await plugin._execute_impl(context)

        # Verify services were used
        mock_cache.get.assert_called_once()
        mock_db.query.assert_called_once()
        mock_cache.set.assert_called_once()

        # Verify result contains expected data
        assert "test message" in result
        assert "mock_db" in result

    @pytest.mark.asyncio
    async def test_constructor_injection_with_cached_result(self):
        """Test plugin with cached result."""
        mock_cache = Mock(spec=CacheService)
        mock_cache.get = AsyncMock(return_value="cached_result")

        plugin = ConstructorInjectionPlugin(
            resources={}, config={"cache_service": mock_cache}
        )

        context = Mock()
        context.message = "test"

        result = await plugin._execute_impl(context)

        # Should return cached result
        assert "[CACHED]" in result
        assert "cached_result" in result

    def test_constructor_injection_default_services(self):
        """Test plugin creates default services when none injected."""
        plugin = ConstructorInjectionPlugin(resources={}, config={})

        # Should have default services
        assert plugin.db_service is not None
        assert plugin.cache_service is not None
        assert isinstance(plugin.db_service, DatabaseService)
        assert isinstance(plugin.cache_service, CacheService)


class TestDualInterfacePlugin:
    """Test dual interface pattern (anthropomorphic vs direct)."""

    def setup_method(self):
        """Set up test plugin."""
        self.plugin = DualInterfacePlugin(resources={}, config={})
        self.context = Mock()

    @pytest.mark.asyncio
    async def test_direct_interface_add_operation(self):
        """Test direct interface with JSON input for addition."""
        self.context.message = json.dumps(
            {"action": "calculate", "operation": "add", "operands": [5, 3]}
        )

        result = await self.plugin._execute_impl(self.context)
        result_data = json.loads(result)

        assert result_data["interface"] == "direct"
        assert result_data["result"] == 8
        assert "add(5, 3)" in result_data["operation"]

    @pytest.mark.asyncio
    async def test_direct_interface_unknown_operation(self):
        """Test direct interface with unknown operation."""
        self.context.message = json.dumps(
            {"action": "calculate", "operation": "unknown", "operands": [1, 2]}
        )

        result = await self.plugin._execute_impl(self.context)
        result_data = json.loads(result)

        assert result_data["interface"] == "direct"
        assert "error" in result_data
        assert "Unknown operation" in result_data["error"]
        assert "available_operations" in result_data

    @pytest.mark.asyncio
    async def test_anthropomorphic_interface_natural_language_add(self):
        """Test anthropomorphic interface with natural language."""
        self.context.message = "What's 5 plus 3?"

        result = await self.plugin._execute_impl(self.context)

        assert "🤖" in result
        assert "5.0 + 3.0 = 8.0" in result

    @pytest.mark.asyncio
    async def test_anthropomorphic_interface_multiply(self):
        """Test anthropomorphic interface with multiplication."""
        self.context.message = "Calculate 7 times 6"

        result = await self.plugin._execute_impl(self.context)

        assert "🤖" in result
        assert "7.0 × 6.0 = 42.0" in result

    @pytest.mark.asyncio
    async def test_anthropomorphic_interface_division_by_zero(self):
        """Test division by zero handling."""
        self.context.message = json.dumps(
            {"action": "calculate", "operation": "divide", "operands": [10, 0]}
        )

        result = await self.plugin._execute_impl(self.context)
        result_data = json.loads(result)

        assert "Error: Division by zero" in str(result_data["result"])

    @pytest.mark.asyncio
    async def test_anthropomorphic_interface_unknown_request(self):
        """Test anthropomorphic interface with unrecognized input."""
        self.context.message = "Tell me a joke"

        result = await self.plugin._execute_impl(self.context)

        assert "🤖" in result
        assert "I understand you want me to do something" in result
        assert "Try:" in result  # Should provide examples


class TestMultiStageAnalyticsPlugin:
    """Test multi-stage plugin support pattern."""

    def setup_method(self):
        """Set up test plugin."""
        self.plugin = MultiStageAnalyticsPlugin(resources={}, config={})

    @pytest.mark.asyncio
    async def test_parse_stage(self):
        """Test PARSE stage processing."""
        context = Mock()
        context.message = "Analyze user engagement trends for sales data"
        context.current_stage = PARSE
        context.metadata = {}

        result = await self.plugin._execute_impl(context)

        assert "[PARSE]" in result
        assert "requirements extracted" in result
        assert "analytics_requirements" in context.metadata

        requirements = context.metadata["analytics_requirements"]
        assert requirements["data_type"] in ["financial", "behavioral", "general"]
        assert requirements["analysis_type"] in [
            "trend_analysis",
            "comparative_analysis",
            "descriptive_analysis",
        ]

    @pytest.mark.asyncio
    async def test_think_stage(self):
        """Test THINK stage processing."""
        context = Mock()
        context.current_stage = THINK
        context.metadata = {
            "analytics_requirements": {
                "data_type": "financial",
                "analysis_type": "trend_analysis",
            }
        }

        result = await self.plugin._execute_impl(context)

        assert "[THINK]" in result
        assert "plan created" in result
        assert "analysis_plan" in context.metadata

        plan = context.metadata["analysis_plan"]
        assert "steps" in plan
        assert "estimated_time" in plan
        assert len(plan["steps"]) > 0

    @pytest.mark.asyncio
    async def test_do_stage(self):
        """Test DO stage processing."""
        context = Mock()
        context.current_stage = DO
        context.metadata = {
            "analysis_plan": {"steps": ["step1", "step2"]},
            "analytics_requirements": {"data_type": "behavioral"},
        }

        result = await self.plugin._execute_impl(context)

        assert "[DO]" in result
        assert "executed" in result
        assert "analysis_results" in context.metadata

        results = context.metadata["analysis_results"]
        assert results["status"] == "completed"
        assert "findings" in results
        assert "confidence_score" in results

    @pytest.mark.asyncio
    async def test_review_stage(self):
        """Test REVIEW stage processing."""
        context = Mock()
        context.current_stage = REVIEW
        context.metadata = {
            "analysis_results": {
                "status": "completed",
                "confidence_score": 0.87,
                "findings": ["test finding"],
            }
        }

        result = await self.plugin._execute_impl(context)

        assert "[REVIEW]" in result
        assert "Quality assessment" in result
        assert "quality_assessment" in context.metadata

        quality = context.metadata["quality_assessment"]
        assert "overall_score" in quality
        assert "approved" in quality
        assert isinstance(quality["overall_score"], float)

    @pytest.mark.asyncio
    async def test_output_stage(self):
        """Test OUTPUT stage processing."""
        context = Mock()
        context.current_stage = OUTPUT
        context.metadata = {
            "analysis_results": {
                "findings": ["Finding 1", "Finding 2"],
                "confidence_score": 0.85,
            },
            "quality_assessment": {"overall_score": 0.8, "approved": True},
        }

        result = await self.plugin._execute_impl(context)

        assert "[OUTPUT]" in result
        assert "Analytics Report Generated" in result
        assert "Executive Summary" in result
        assert "Key Findings" in result
        assert "Quality Score" in result
        assert "PARSE → THINK → DO → REVIEW → OUTPUT" in result

    @pytest.mark.asyncio
    async def test_stage_data_flow(self):
        """Test data flows correctly between stages."""
        context = Mock()
        context.metadata = {}

        # PARSE stage
        context.message = "Analyze sales trends"
        context.current_stage = PARSE
        await self.plugin._execute_impl(context)

        # THINK stage should use PARSE results
        context.current_stage = THINK
        await self.plugin._execute_impl(context)

        # DO stage should use THINK results
        context.current_stage = DO
        await self.plugin._execute_impl(context)

        # REVIEW stage should use DO results
        context.current_stage = REVIEW
        await self.plugin._execute_impl(context)

        # OUTPUT stage should use all previous results
        context.current_stage = OUTPUT
        result = await self.plugin._execute_impl(context)

        # Final result should contain comprehensive report
        assert "Analytics Report Generated" in result
        assert len(result) > 200  # Should be a substantial report


class TestEnvironmentSubstitutionPlugin:
    """Test environment variable substitution pattern."""

    def setup_method(self):
        """Set up test environment."""
        # Set test environment variables
        os.environ["TEST_VAR"] = "test_value"
        os.environ["APP_NAME"] = "TestApp"
        os.environ["PORT"] = "8080"
        os.environ["EMPTY_VAR"] = ""

    def teardown_method(self):
        """Clean up test environment."""
        test_vars = ["TEST_VAR", "APP_NAME", "PORT", "EMPTY_VAR", "NEW_VAR"]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

    @pytest.mark.asyncio
    async def test_basic_substitution(self):
        """Test basic environment variable substitution."""
        plugin = EnvironmentSubstitutionPlugin(resources={}, config={})

        context = Mock()
        context.message = "Hello from ${APP_NAME}!"

        result = await plugin._execute_impl(context)

        assert result == "Hello from TestApp!"

    @pytest.mark.asyncio
    async def test_multiple_substitutions(self):
        """Test multiple environment variable substitutions."""
        plugin = EnvironmentSubstitutionPlugin(resources={}, config={})

        context = Mock()
        context.message = "${APP_NAME} is running on port ${PORT}"

        result = await plugin._execute_impl(context)

        assert result == "TestApp is running on port 8080"

    @pytest.mark.asyncio
    async def test_default_value_substitution(self):
        """Test substitution with default values."""
        plugin = EnvironmentSubstitutionPlugin(resources={}, config={})

        context = Mock()
        context.message = "API: ${MISSING_VAR:https://api.default.com}"

        result = await plugin._execute_impl(context)

        assert result == "API: https://api.default.com"

    @pytest.mark.asyncio
    async def test_empty_var_with_default(self):
        """Test substitution with empty variable and default."""
        plugin = EnvironmentSubstitutionPlugin(resources={}, config={})

        context = Mock()
        context.message = "Value: ${EMPTY_VAR:-default_for_empty}"

        result = await plugin._execute_impl(context)

        assert result == "Value: default_for_empty"

    @pytest.mark.asyncio
    async def test_missing_required_variable_error(self):
        """Test error handling for missing required variables."""
        # This should raise during initialization when allow_missing_variables is False
        with pytest.raises(ValueError) as exc_info:
            EnvironmentSubstitutionPlugin(
                resources={},
                config={
                    "required_variables": ["REQUIRED_VAR"],
                    "allow_missing_variables": False,
                },
            )

        assert "Required environment variables missing: REQUIRED_VAR" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_allow_missing_variables(self):
        """Test allowing missing variables."""
        plugin = EnvironmentSubstitutionPlugin(
            resources={}, config={"allow_missing_variables": True}
        )

        context = Mock()
        context.message = "Value: ${MISSING_VAR}"

        result = await plugin._execute_impl(context)

        # Should return original placeholder when missing vars are allowed
        assert result == "Value: ${MISSING_VAR}"

    @pytest.mark.asyncio
    async def test_nested_substitution(self):
        """Test nested environment variable substitution."""
        os.environ["BASE_URL"] = "https://${APP_NAME}.com"

        plugin = EnvironmentSubstitutionPlugin(resources={}, config={})

        context = Mock()
        context.message = "Visit ${BASE_URL}"

        result = await plugin._execute_impl(context)

        assert result == "Visit https://TestApp.com"

    @pytest.mark.asyncio
    async def test_env_file_loading(self):
        """Test loading environment variables from .env file."""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("NEW_VAR=from_env_file\n")
            f.write('QUOTED_VAR="quoted_value"\n')
            f.write("# This is a comment\n")
            f.write("ANOTHER_VAR=another_value\n")
            env_file_path = f.name

        try:
            plugin = EnvironmentSubstitutionPlugin(
                resources={}, config={"env_file_path": env_file_path}
            )

            context = Mock()
            context.message = "${NEW_VAR} and ${QUOTED_VAR}"

            result = await plugin._execute_impl(context)

            assert result == "from_env_file and quoted_value"

        finally:
            # Clean up temp file
            Path(env_file_path).unlink()

    def test_get_environment_info(self):
        """Test getting environment configuration info."""
        plugin = EnvironmentSubstitutionPlugin(
            resources={},
            config={
                "required_variables": ["TEST_VAR", "APP_NAME"],
                "allow_missing_variables": True,
            },
        )

        info = plugin.get_environment_info()

        assert "required_variables" in info
        assert "required_vars_present" in info
        assert "substitution_pattern" in info
        assert info["allow_missing_vars"] is True
        assert "TEST_VAR" in info["required_vars_present"]
        assert "APP_NAME" in info["required_vars_present"]


class TestPatternIntegration:
    """Integration tests for all patterns working together."""

    @pytest.mark.asyncio
    async def test_all_patterns_importable(self):
        """Test that all pattern plugins can be imported and instantiated."""
        plugins = [
            ConstructorInjectionPlugin,
            DualInterfacePlugin,
            MultiStageAnalyticsPlugin,
            EnvironmentSubstitutionPlugin,
        ]

        for plugin_class in plugins:
            plugin = plugin_class(resources={}, config={})
            assert plugin is not None
            assert hasattr(plugin, "supported_stages")
            assert hasattr(plugin, "_execute_impl")

    def test_pattern_supported_stages(self):
        """Test that patterns support appropriate stages."""
        # Constructor injection - THINK stage
        plugin1 = ConstructorInjectionPlugin(resources={}, config={})
        assert THINK in plugin1.supported_stages

        # Dual interface - DO stage
        plugin2 = DualInterfacePlugin(resources={}, config={})
        assert DO in plugin2.supported_stages

        # Multi-stage - multiple stages
        plugin3 = MultiStageAnalyticsPlugin(resources={}, config={})
        expected_stages = [PARSE, THINK, DO, REVIEW, OUTPUT]
        for stage in expected_stages:
            assert stage in plugin3.supported_stages

        # Environment substitution - INPUT/PARSE stages
        plugin4 = EnvironmentSubstitutionPlugin(resources={}, config={})
        assert INPUT in plugin4.supported_stages or PARSE in plugin4.supported_stages
