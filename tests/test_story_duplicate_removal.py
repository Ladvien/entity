"""
Tests for Story 2: Remove Duplicate GPT-OSS Plugin Implementations

This test file verifies that:
1. Duplicate plugin implementation files have been removed
2. The __init__.py properly imports from the compatibility layer
3. All expected plugins are still importable through the gpt_oss module
4. Deprecation warnings are properly issued
5. No direct imports from removed files exist in the codebase
"""

import warnings
from pathlib import Path

import pytest


class TestStory2DuplicateRemoval:
    """Test Story 2: Remove Duplicate GPT-OSS Plugin Implementations."""

    EXPECTED_PLUGINS = [
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

    REMOVED_FILES = [
        "reasoning_trace.py",
        "structured_output.py",
        "developer_override.py",
        "adaptive_reasoning.py",
        "native_tools.py",
        "multi_channel_aggregator.py",
        "harmony_safety_filter.py",
        "function_schema_registry.py",
        "reasoning_analytics_dashboard.py",
    ]

    @pytest.fixture
    def gpt_oss_dir(self):
        """Get the gpt_oss directory path."""
        return Path(__file__).parent.parent / "src" / "entity" / "plugins" / "gpt_oss"

    def test_duplicate_files_removed(self, gpt_oss_dir):
        """Test that all duplicate plugin implementation files have been removed."""
        for filename in self.REMOVED_FILES:
            file_path = gpt_oss_dir / filename
            assert (
                not file_path.exists()
            ), f"Duplicate file {filename} should be removed"

    def test_init_file_exists(self, gpt_oss_dir):
        """Test that __init__.py still exists."""
        init_file = gpt_oss_dir / "__init__.py"
        assert init_file.exists(), "__init__.py should be preserved"

    def test_only_init_file_remains(self, gpt_oss_dir):
        """Test that only __init__.py remains in the gpt_oss directory."""
        python_files = list(gpt_oss_dir.glob("*.py"))
        assert (
            len(python_files) == 1
        ), f"Only __init__.py should remain, found: {python_files}"
        assert python_files[0].name == "__init__.py"

    def test_init_file_imports_from_compat(self, gpt_oss_dir):
        """Test that __init__.py imports from gpt_oss_compat module."""
        init_file = gpt_oss_dir / "__init__.py"
        content = init_file.read_text()

        assert (
            "from ..gpt_oss_compat import" in content
        ), "Should import from gpt_oss_compat"

        # Check that all expected plugins are imported
        for plugin in self.EXPECTED_PLUGINS:
            assert plugin in content, f"Plugin {plugin} should be imported"

    def test_init_file_has_deprecation_warning(self, gpt_oss_dir):
        """Test that __init__.py contains deprecation warning."""
        init_file = gpt_oss_dir / "__init__.py"
        content = init_file.read_text()

        assert "DEPRECATED" in content, "Should have deprecation notice"
        assert "warnings.warn" in content, "Should emit deprecation warning"
        assert "entity-plugin-gpt-oss" in content, "Should mention new package"

    def test_init_file_maintains_api(self, gpt_oss_dir):
        """Test that __init__.py maintains the same public API."""
        init_file = gpt_oss_dir / "__init__.py"
        content = init_file.read_text()

        assert "__all__" in content, "Should define __all__"

        # Check that all expected plugins are in __all__
        for plugin in self.EXPECTED_PLUGINS:
            assert (
                f'"{plugin}"' in content or f"'{plugin}'" in content
            ), f"Plugin {plugin} should be in __all__"

    def test_deprecation_warning_issued_on_import(self):
        """Test that importing from gpt_oss issues a deprecation warning."""
        # Clear any existing modules to ensure fresh import
        import sys

        modules_to_remove = [
            k for k in sys.modules.keys() if k.startswith("entity.plugins.gpt_oss")
        ]
        for module in modules_to_remove:
            if module != "entity.plugins.gpt_oss_compat":  # Keep compat module
                del sys.modules[module]

        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")  # Capture all warnings

            try:
                # This should trigger deprecation warning
                from entity.plugins import gpt_oss  # noqa: F401

                # Filter for our deprecation warnings (ignore other warnings like Pydantic)
                our_warnings = [
                    w
                    for w in warning_list
                    if issubclass(w.category, DeprecationWarning)
                    and "entity.plugins.gpt_oss" in str(w.message)
                ]

                assert (
                    len(our_warnings) > 0
                ), f"Should issue deprecation warning. Got warnings: {[str(w.message) for w in warning_list]}"

                # Check warning content
                warning_msg = str(our_warnings[0].message)
                assert "deprecated" in warning_msg.lower()
                assert "entity-plugin-gpt-oss" in warning_msg

            except ImportError as e:
                # If the compatibility layer can't import the package, that's expected
                # in test environments where entity-plugin-gpt-oss is not installed
                assert "entity-plugin-gpt-oss" in str(
                    e
                ) or "entity_plugin_gpt_oss" in str(e)

    def test_compatibility_layer_fallback_behavior(self):
        """Test that compatibility layer provides helpful error when package not available."""
        # Since entity-plugin-gpt-oss is not installed in the test environment,
        # we should get a helpful error message when trying to use the plugins

        try:
            from entity.plugins.gpt_oss import ReasoningTracePlugin

            # Try to instantiate to trigger the import error
            ReasoningTracePlugin({}, {})  # This should trigger the error

            # If we get here, the package is installed - skip the test
            pytest.skip("entity-plugin-gpt-oss package is installed")

        except ImportError as exc_info:
            error_msg = str(exc_info)
            assert "entity-plugin-gpt-oss" in error_msg
            assert "pip install" in error_msg

    def test_no_direct_imports_in_tests(self):
        """Test that no test files directly import from removed plugin files."""
        test_dir = Path(__file__).parent / "plugins" / "gpt_oss"

        if not test_dir.exists():
            pytest.skip("GPT-OSS test directory not found")

        # Check all test files
        test_files = list(test_dir.glob("test_*.py"))

        for test_file in test_files:
            content = test_file.read_text()

            # Should not import directly from individual plugin files
            for removed_file in self.REMOVED_FILES:
                module_name = removed_file.replace(".py", "")
                direct_import_pattern = (
                    f"from entity.plugins.gpt_oss.{module_name} import"
                )

                assert (
                    direct_import_pattern not in content
                ), f"Test file {test_file} should not directly import from {module_name}"

    def test_plugin_classes_still_importable(self):
        """Test that all plugin classes are still importable through the main module."""
        # This test verifies the public API is maintained
        try:
            from entity.plugins.gpt_oss import (
                AdaptiveReasoningPlugin,
                DeveloperOverridePlugin,
                FunctionSchemaRegistryPlugin,
                GPTOSSToolOrchestrator,
                HarmonySafetyFilterPlugin,
                MultiChannelAggregatorPlugin,
                ReasoningAnalyticsDashboardPlugin,
                ReasoningTracePlugin,
                StructuredOutputPlugin,
            )

            # Verify all classes are imported
            imported_classes = [
                ReasoningTracePlugin,
                StructuredOutputPlugin,
                DeveloperOverridePlugin,
                AdaptiveReasoningPlugin,
                GPTOSSToolOrchestrator,
                MultiChannelAggregatorPlugin,
                HarmonySafetyFilterPlugin,
                FunctionSchemaRegistryPlugin,
                ReasoningAnalyticsDashboardPlugin,
            ]

            for cls in imported_classes:
                assert cls is not None, f"Class {cls.__name__} should be importable"
                assert hasattr(
                    cls, "__name__"
                ), f"Class {cls} should have __name__ attribute"

        except ImportError as e:
            # Expected if entity-plugin-gpt-oss is not installed
            if "entity-plugin-gpt-oss" in str(e) or "entity_plugin_gpt_oss" in str(e):
                pytest.skip(f"Skipping import test - package not installed: {e}")
            else:
                raise

    def test_gpt_oss_compat_module_exists(self):
        """Test that the gpt_oss_compat module exists and has compatibility shims."""
        try:
            import entity.plugins.gpt_oss_compat

            # Check that compatibility shims exist for expected plugins
            expected_shims = [
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

            for plugin_name in expected_shims:
                assert hasattr(
                    entity.plugins.gpt_oss_compat, plugin_name
                ), f"Compatibility shim for {plugin_name} should exist"

        except ImportError as e:
            pytest.fail(f"gpt_oss_compat module should be importable: {e}")

    def test_story_2_acceptance_criteria(self, gpt_oss_dir):
        """Test all Story 2 acceptance criteria are met."""
        # ✓ Delete all 9 individual plugin implementation files
        for filename in self.REMOVED_FILES:
            assert not (
                gpt_oss_dir / filename
            ).exists(), f"File {filename} should be deleted"

        # ✓ Keep only the __init__.py file in the gpt_oss directory
        py_files = list(gpt_oss_dir.glob("*.py"))
        assert len(py_files) == 1 and py_files[0].name == "__init__.py"

        # ✓ Update __init__.py to import from gpt_oss_compat module
        init_content = (gpt_oss_dir / "__init__.py").read_text()
        assert "from ..gpt_oss_compat import" in init_content

        # ✓ Ensure __init__.py maintains the same public API
        for plugin in self.EXPECTED_PLUGINS:
            assert plugin in init_content

        # ✓ Add clear deprecation warnings in __init__.py
        assert "DEPRECATED" in init_content
        assert "warnings.warn" in init_content

        # ✓ Verify no other parts of the codebase directly import from the deleted files
        # This is tested in test_no_direct_imports_in_tests


class TestStory2ComplianceAndCleanup:
    """Additional compliance and cleanup tests for Story 2."""

    def test_codebase_search_no_direct_imports(self):
        """Search entire codebase for any remaining direct imports from removed files."""
        import subprocess

        base_dir = Path(__file__).parent.parent

        removed_modules = [
            "reasoning_trace",
            "structured_output",
            "developer_override",
            "adaptive_reasoning",
            "native_tools",
            "multi_channel_aggregator",
            "harmony_safety_filter",
            "function_schema_registry",
            "reasoning_analytics_dashboard",
        ]

        for module in removed_modules:
            # Search for direct imports
            pattern = f"from entity.plugins.gpt_oss.{module} import"

            try:
                result = subprocess.run(
                    [
                        "grep",
                        "-r",
                        pattern,
                        str(base_dir / "src"),
                        str(base_dir / "tests"),
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:  # Found matches
                    matches = result.stdout.strip()
                    pytest.fail(
                        f"Found direct imports from removed module {module}:\n{matches}"
                    )

            except FileNotFoundError:
                # grep not available, skip this test
                pytest.skip("grep not available for codebase search")

    def test_implementation_completeness(self):
        """Test that Story 2 implementation is complete and functional."""
        # This test serves as a final verification that all parts work together

        # 1. Files are removed ✓
        gpt_oss_dir = (
            Path(__file__).parent.parent / "src" / "entity" / "plugins" / "gpt_oss"
        )
        removed_files = [
            "reasoning_trace.py",
            "structured_output.py",
            "developer_override.py",
            "adaptive_reasoning.py",
            "native_tools.py",
            "multi_channel_aggregator.py",
            "harmony_safety_filter.py",
            "function_schema_registry.py",
            "reasoning_analytics_dashboard.py",
        ]

        for filename in removed_files:
            assert not (gpt_oss_dir / filename).exists()

        # 2. Compatibility layer is functional ✓
        try:
            # Should work through compatibility layer (or fail with helpful error)
            import entity.plugins.gpt_oss_compat

            # Check that compatibility shims are callable
            assert callable(entity.plugins.gpt_oss_compat.ReasoningTracePlugin)
        except ImportError:
            pytest.fail("Compatibility layer should be importable")

        # 3. Public API is maintained ✓
        init_file = gpt_oss_dir / "__init__.py"
        content = init_file.read_text()
        expected_plugins = [
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

        for plugin in expected_plugins:
            assert plugin in content, f"Plugin {plugin} should be in __init__.py"

        print("✅ Story 2 implementation is complete and functional!")
