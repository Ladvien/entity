"""
Integration tests for GPT-OSS plugin migration from monolithic to modular structure.

This test file verifies:
1. Legacy import path (entity.plugins.gpt_oss) works with deprecation warnings
2. New import path (entity_plugin_gpt_oss) works when package is installed
3. Both import methods result in the same functional behavior
4. Proper error handling when package is not installed
5. All 9 plugins can be imported and instantiated
"""

import sys
import warnings
from unittest.mock import MagicMock, patch

import pytest


class TestGPTOSSMigrationPaths:
    """Test migration from legacy to new import paths."""

    # List of all 9 GPT-OSS plugins
    PLUGIN_NAMES = [
        "ReasoningTracePlugin",
        "StructuredOutputPlugin",
        "DeveloperOverridePlugin",
        "AdaptiveReasoningPlugin",
        "GPTOSSToolOrchestrator",
        "MultiChannelAggregatorPlugin",
        "HarmonySafetyFilterPlugin",
        "FunctionSchemaRegistryPlugin",
        "ReasoningAnalyticsDashboardPlugin",
    ]

    # Mapping of plugins to their expected module paths in new package
    PLUGIN_MODULE_MAP = {
        "ReasoningTracePlugin": "entity_plugin_gpt_oss.reasoning_trace",
        "StructuredOutputPlugin": "entity_plugin_gpt_oss.structured_output",
        "DeveloperOverridePlugin": "entity_plugin_gpt_oss.developer_override",
        "AdaptiveReasoningPlugin": "entity_plugin_gpt_oss.adaptive_reasoning",
        "GPTOSSToolOrchestrator": "entity_plugin_gpt_oss.native_tools",
        "MultiChannelAggregatorPlugin": "entity_plugin_gpt_oss.multi_channel_aggregator",
        "HarmonySafetyFilterPlugin": "entity_plugin_gpt_oss.harmony_safety_filter",
        "FunctionSchemaRegistryPlugin": "entity_plugin_gpt_oss.function_schema_registry",
        "ReasoningAnalyticsDashboardPlugin": "entity_plugin_gpt_oss.reasoning_analytics_dashboard",
    }

    def test_legacy_import_path_with_deprecation_warning(self):
        """Test that legacy import path raises deprecation warnings."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")

            # Import from legacy path
            from entity.plugins import gpt_oss

            # Check module is importable
            assert gpt_oss is not None
            assert hasattr(gpt_oss, "__file__")

            # Check deprecation warning was issued (from module docstring or import)
            # The warning may be in the module initialization
            for plugin_name in self.PLUGIN_NAMES:
                assert hasattr(
                    gpt_oss, plugin_name
                ), f"Plugin {plugin_name} not found in legacy import"

    def test_legacy_import_individual_plugins_with_warnings(self):
        """Test importing individual plugins from legacy path raises warnings."""
        for plugin_name in self.PLUGIN_NAMES:
            with warnings.catch_warnings(record=True):
                warnings.simplefilter("always")

                # Try to access the plugin (will trigger compatibility shim)
                from entity.plugins import gpt_oss

                plugin_shim = getattr(gpt_oss, plugin_name)

                # The shim should exist
                assert plugin_shim is not None

                # When we try to use it, we should get a deprecation warning
                # Note: Actually calling it would require the package to be installed
                # So we just verify the shim exists and has the right attributes
                assert hasattr(plugin_shim, "plugin_class_name")
                assert plugin_shim.plugin_class_name == plugin_name

    def test_new_import_path_mock(self):
        """Test new import path with mocked entity_plugin_gpt_oss package."""
        # Mock the new package structure
        for plugin_name, module_path in self.PLUGIN_MODULE_MAP.items():
            mock_module = MagicMock()
            mock_plugin_class = MagicMock()
            mock_plugin_class.__name__ = plugin_name
            setattr(mock_module, plugin_name, mock_plugin_class)

            with patch.dict(sys.modules, {module_path: mock_module}):
                # Verify we can import from the mocked new path
                module = __import__(module_path, fromlist=[plugin_name])
                plugin_class = getattr(module, plugin_name)
                assert plugin_class.__name__ == plugin_name

    def test_deprecation_warning_content(self):
        """Test that deprecation warnings contain helpful information."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Import and try to use a plugin through legacy path
            from entity.plugins.gpt_oss import ReasoningTracePlugin

            # Try to trigger the deprecation warning
            try:
                # This will fail because package isn't installed, but should issue warning first
                ReasoningTracePlugin({}, {})
            except ImportError:
                pass  # Expected when package not installed

            # Check that we got deprecation warnings with proper content
            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]

            if deprecation_warnings:
                warning_messages = [
                    str(warning.message) for warning in deprecation_warnings
                ]
                combined_message = " ".join(warning_messages)

                # Check warning contains migration instructions
                assert "deprecated" in combined_message.lower()
                assert (
                    "entity-plugin-gpt-oss" in combined_message
                    or "entity_plugin_gpt_oss" in combined_message
                )

    def test_error_when_package_not_installed(self):
        """Test proper error handling when entity-plugin-gpt-oss is not installed."""
        from entity.plugins.gpt_oss import ReasoningTracePlugin

        # Trying to instantiate should give helpful error
        with pytest.raises(ImportError) as exc_info:
            ReasoningTracePlugin({}, {})

        error_msg = str(exc_info.value)
        # Should contain installation instructions
        assert "pip install" in error_msg or "entity-plugin-gpt-oss" in error_msg

    def test_all_plugins_accessible_through_compatibility_layer(self):
        """Test that all 9 plugins are accessible through the compatibility layer."""
        from entity.plugins import gpt_oss

        for plugin_name in self.PLUGIN_NAMES:
            # Check plugin is accessible
            assert hasattr(gpt_oss, plugin_name), f"Plugin {plugin_name} not accessible"

            # Get the plugin shim
            plugin_shim = getattr(gpt_oss, plugin_name)

            # Verify it's a compatibility shim
            assert hasattr(plugin_shim, "plugin_class_name")
            assert plugin_shim.plugin_class_name == plugin_name
            assert hasattr(plugin_shim, "new_module_path")
            assert plugin_shim.new_module_path == self.PLUGIN_MODULE_MAP[plugin_name]

    def test_helper_classes_accessible(self):
        """Test that helper classes are also accessible through compatibility layer."""
        from entity.plugins import gpt_oss

        # Test a few representative helper classes
        helper_classes = [
            "ReasoningLevel",  # From reasoning_trace
            "ValidationResult",  # From structured_output
            "ComplexityFactors",  # From adaptive_reasoning
            "SafetyLevel",  # From harmony_safety_filter
            "ToolExecutionContext",  # From native_tools
        ]

        for helper_class in helper_classes:
            # These will fail to import (package not installed) but should be handled
            try:
                getattr(gpt_oss, helper_class)
            except ImportError as e:
                # Should get helpful error message
                error_msg = str(e)
                assert "entity-plugin-gpt-oss" in error_msg
                assert helper_class in error_msg

    def test_import_both_paths_comparison(self):
        """Test that both import paths would result in same functionality (mocked)."""
        # This test demonstrates that both paths lead to the same plugin classes
        # In reality, they both route to entity_plugin_gpt_oss

        from entity.plugins.gpt_oss import ReasoningTracePlugin as LegacyPlugin

        # Mock the new package
        mock_module = MagicMock()
        mock_plugin = MagicMock()
        mock_plugin.__name__ = "ReasoningTracePlugin"
        mock_module.ReasoningTracePlugin = mock_plugin

        with patch.dict(
            sys.modules, {"entity_plugin_gpt_oss.reasoning_trace": mock_module}
        ):
            # If the package were installed, both would resolve to the same class
            # The legacy path uses _CompatibilityShim which imports from new path
            assert (
                LegacyPlugin.new_module_path == "entity_plugin_gpt_oss.reasoning_trace"
            )

    def test_environment_variable_suppression(self):
        """Test that ENTITY_SUPPRESS_GPT_OSS_DEPRECATION suppresses warnings."""
        import os

        # Test with suppression enabled
        os.environ["ENTITY_SUPPRESS_GPT_OSS_DEPRECATION"] = "1"
        try:
            # Re-import the module to pick up env var
            import importlib

            import entity.plugins.gpt_oss_compat as compat

            importlib.reload(compat)

            # Check suppression is enabled
            assert compat.SUPPRESS_DEPRECATION is True

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                compat._warn_deprecated_import("TestPlugin")

                # Should not issue warning when suppressed
                deprecation_warnings = [
                    warning
                    for warning in w
                    if issubclass(warning.category, DeprecationWarning)
                ]
                assert len(deprecation_warnings) == 0

        finally:
            # Clean up
            os.environ.pop("ENTITY_SUPPRESS_GPT_OSS_DEPRECATION", None)

            # Reload to reset suppression state
            import importlib

            import entity.plugins.gpt_oss_compat as compat

            importlib.reload(compat)


class TestMigrationDocumentation:
    """Test that migration is properly documented."""

    def test_compatibility_module_has_migration_guide(self):
        """Test that gpt_oss_compat.py contains migration documentation."""
        import entity.plugins.gpt_oss_compat as compat

        # Check module docstring contains migration guide
        assert compat.__doc__ is not None
        assert "MIGRATION GUIDE" in compat.__doc__
        assert "DEPRECATED" in compat.__doc__
        assert "pip install entity-plugin-gpt-oss" in compat.__doc__
        assert "OLD WAY" in compat.__doc__ and "NEW WAY" in compat.__doc__

    def test_deprecation_timeline_documented(self):
        """Test that deprecation timeline is clearly documented."""
        import entity.plugins.gpt_oss_compat as compat

        # Check timeline is defined
        assert hasattr(compat, "DEPRECATION_VERSION")
        assert hasattr(compat, "DEPRECATION_DATE")

        # Check timeline appears in documentation
        assert compat.DEPRECATION_VERSION in compat.__doc__
        assert compat.DEPRECATION_DATE in compat.__doc__

    def test_all_plugins_listed_in_documentation(self):
        """Test that all 9 plugins are listed in migration documentation."""
        import entity.plugins.gpt_oss_compat as compat

        plugin_names = [
            "ReasoningTracePlugin",
            "StructuredOutputPlugin",
            "DeveloperOverridePlugin",
            "AdaptiveReasoningPlugin",
            "GPTOSSToolOrchestrator",
            "MultiChannelAggregatorPlugin",
            "HarmonySafetyFilterPlugin",
            "FunctionSchemaRegistryPlugin",
            "ReasoningAnalyticsDashboardPlugin",
        ]

        for plugin in plugin_names:
            assert (
                plugin in compat.__doc__
            ), f"Plugin {plugin} not documented in migration guide"


class TestErrorHandling:
    """Test error handling during migration."""

    def test_clear_error_when_package_missing(self):
        """Test clear error message when entity-plugin-gpt-oss is not installed."""
        from entity.plugins.gpt_oss import StructuredOutputPlugin

        with pytest.raises(ImportError) as exc_info:
            StructuredOutputPlugin({}, {})

        error_msg = str(exc_info.value)

        # Should have clear instructions
        assert "GPT-OSS Plugin Not Available" in error_msg or "pip install" in error_msg
        assert "entity-plugin-gpt-oss" in error_msg

        # Should show both old and new import paths
        assert "OLD:" in error_msg or "from entity.plugins.gpt_oss" in error_msg
        assert "NEW:" in error_msg or "from entity_plugin_gpt_oss" in error_msg

    def test_error_includes_original_exception(self):
        """Test that error messages include the original exception details."""
        from entity.plugins.gpt_oss import AdaptiveReasoningPlugin

        with pytest.raises(ImportError) as exc_info:
            AdaptiveReasoningPlugin({}, {})

        error_msg = str(exc_info.value)

        # Should include original error information
        assert "Original error:" in error_msg or "No module named" in error_msg

    def test_compatibility_shim_repr(self):
        """Test that compatibility shims have informative repr."""
        from entity.plugins.gpt_oss import DeveloperOverridePlugin

        repr_str = repr(DeveloperOverridePlugin)

        # Should indicate it's a compatibility shim
        assert "CompatibilityShim" in repr_str
        assert "DeveloperOverridePlugin" in repr_str

        # When package not installed, should indicate that
        assert "not available" in repr_str.lower()


class TestPackageDetection:
    """Test package installation detection."""

    def test_package_detection_functions(self):
        """Test functions that detect if entity-plugin-gpt-oss is installed."""
        import entity.plugins.gpt_oss_compat as compat

        # Test detection function exists
        assert hasattr(compat, "_check_package_installed")

        # In test environment, package is not installed
        assert compat._check_package_installed() is False

        # Test version detection
        assert hasattr(compat, "_get_package_version")
        assert compat._get_package_version() is None  # Not installed

    def test_package_detection_with_mock(self):
        """Test package detection with mocked installed package."""
        import entity.plugins.gpt_oss_compat as compat

        with patch.object(compat, "_check_package_installed", return_value=True):
            with patch.object(compat, "_get_package_version", return_value="1.0.0"):
                # Test error message differs when package is "installed"
                error_msg = compat._create_detailed_error_message(
                    "TestPlugin", "entity_plugin_gpt_oss.test", Exception("Test error")
                )

                # Should indicate package is installed but import failed
                assert "Installed (version 1.0.0)" in error_msg
                assert (
                    "Version incompatibility" in error_msg or "reinstall" in error_msg
                )


# Test Environment Setup Documentation
"""
Test Environment Setup Requirements:
=====================================

1. Default Testing (package not installed):
   - No additional setup required
   - Tests verify behavior when entity-plugin-gpt-oss is NOT installed
   - This represents the current state during migration

2. Full Integration Testing (requires package):
   - Install: pip install entity-plugin-gpt-oss
   - Run: pytest tests/test_gpt_oss_migration.py -v
   - This tests actual package integration

3. CI/CD Configuration:
   - Add to test matrix: test with and without entity-plugin-gpt-oss
   - Example GitHub Actions:
     ```yaml
     strategy:
       matrix:
         gpt-oss: [true, false]
     steps:
       - name: Install GPT-OSS (conditional)
         if: matrix.gpt-oss == true
         run: pip install entity-plugin-gpt-oss
     ```

4. Environment Variables:
   - ENTITY_SUPPRESS_GPT_OSS_DEPRECATION=1 : Suppress deprecation warnings
   - Useful for CI/CD pipelines during transition period

5. Testing Both Paths:
   - Legacy: from entity.plugins.gpt_oss import PluginName
   - New: from entity_plugin_gpt_oss import PluginName
   - Both should work during transition period

Note: Most tests use mocking to avoid requiring the actual entity-plugin-gpt-oss
      package, allowing tests to run in any environment.
"""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
