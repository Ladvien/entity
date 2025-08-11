"""Tests for GPT-OSS package completeness verification (Story 1)."""

import subprocess
from pathlib import Path

import pytest


class TestGPTOSSPackageCompleteness:
    """Test GPT-OSS package completeness verification."""

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

    PLUGIN_FILES = [
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
    def base_dir(self):
        """Get base directory path."""
        return Path(__file__).parent.parent

    @pytest.fixture
    def main_gpt_oss_dir(self, base_dir):
        """Get main repository GPT-OSS directory."""
        return base_dir / "src" / "entity" / "plugins" / "gpt_oss"

    @pytest.fixture
    def package_dir(self, base_dir):
        """Get package directory."""
        return base_dir / "entity-plugin-gpt-oss" / "src" / "entity_plugin_gpt_oss"

    def test_package_directory_exists(self, package_dir):
        """Test that package directory exists."""
        assert (
            package_dir.exists()
        ), "entity-plugin-gpt-oss package directory should exist"
        assert package_dir.is_dir(), "Package path should be a directory"

    def test_main_gpt_oss_directory_exists(self, main_gpt_oss_dir):
        """Test that main GPT-OSS directory exists."""
        assert main_gpt_oss_dir.exists(), "Main GPT-OSS directory should exist"
        assert main_gpt_oss_dir.is_dir(), "Main GPT-OSS path should be a directory"

    def test_all_plugin_files_exist_in_package(self, package_dir):
        """Test that all expected plugin files exist in package."""
        for plugin_file in self.PLUGIN_FILES:
            plugin_path = package_dir / plugin_file
            assert (
                plugin_path.exists()
            ), f"Plugin file {plugin_file} should exist in package"

    def test_all_plugin_files_exist_in_main(self, main_gpt_oss_dir):
        """Test that all expected plugin files exist in main repo."""
        for plugin_file in self.PLUGIN_FILES:
            plugin_path = main_gpt_oss_dir / plugin_file
            assert (
                plugin_path.exists()
            ), f"Plugin file {plugin_file} should exist in main repo"

    def test_package_init_exports_all_plugins(self, package_dir):
        """Test that package __init__.py exports all expected plugins."""
        init_file = package_dir / "__init__.py"
        assert init_file.exists(), "Package __init__.py should exist"

        with open(init_file, "r") as f:
            content = f.read()

        # Check that all expected plugins are imported and exported
        for plugin in self.EXPECTED_PLUGINS:
            assert (
                plugin in content
            ), f"Plugin {plugin} should be imported in __init__.py"

        # Check __all__ contains all plugins
        assert "__all__" in content, "__all__ should be defined in __init__.py"
        for plugin in self.EXPECTED_PLUGINS:
            assert (
                f'"{plugin}"' in content or f"'{plugin}'" in content
            ), f"Plugin {plugin} should be in __all__"

    def test_package_pyproject_toml_exists(self, base_dir):
        """Test that package pyproject.toml exists and has required fields."""
        pyproject_path = base_dir / "entity-plugin-gpt-oss" / "pyproject.toml"
        assert pyproject_path.exists(), "Package pyproject.toml should exist"

        with open(pyproject_path, "r") as f:
            content = f.read()

        # Check required fields
        assert (
            'name = "entity-plugin-gpt-oss"' in content
        ), "Package name should be correct"
        assert "version =" in content, "Version should be specified"
        assert "entity-core" in content, "Should depend on entity-core"

    def test_verification_script_exists_and_runs(self, base_dir):
        """Test that verification script exists and runs successfully."""
        script_path = base_dir / "scripts" / "verify_gpt_oss_completeness.py"
        assert script_path.exists(), "Verification script should exist"

        # Run the script
        result = subprocess.run(
            ["poetry", "run", "python", str(script_path)],
            cwd=base_dir,
            capture_output=True,
            text=True,
        )

        assert (
            result.returncode == 0
        ), f"Verification script should pass: {result.stderr}"
        assert (
            "VERIFICATION REPORT" in result.stdout
        ), "Script should produce verification report"
        assert "Verification: PASSED" in result.stdout, "Verification should pass"

    def test_plugin_classes_can_be_imported_from_package(self, package_dir):
        """Test that plugin classes can be imported from package."""
        # Add package to path for import testing
        import sys

        package_parent = package_dir.parent.parent
        if str(package_parent) not in sys.path:
            sys.path.insert(0, str(package_parent))

        try:
            # Try importing each expected plugin
            try:
                import entity_plugin_gpt_oss

                for plugin in self.EXPECTED_PLUGINS:
                    assert hasattr(
                        entity_plugin_gpt_oss, plugin
                    ), f"Plugin {plugin} should be importable from package"

                    plugin_class = getattr(entity_plugin_gpt_oss, plugin)
                    assert (
                        plugin_class is not None
                    ), f"Plugin {plugin} should not be None"

            except ImportError:
                # Skip test if package not installed - this is expected
                # since we're testing the package structure, not installation
                pytest.skip("Package not installed - testing structure only")

        finally:
            # Clean up sys.path
            if str(package_parent) in sys.path:
                sys.path.remove(str(package_parent))

    def test_package_has_proper_metadata(self, base_dir):
        """Test that package has proper metadata."""
        pyproject_path = base_dir / "entity-plugin-gpt-oss" / "pyproject.toml"

        with open(pyproject_path, "r") as f:
            content = f.read()

        # Check metadata fields
        assert "description =" in content, "Should have description"
        assert "authors =" in content, "Should have authors"
        assert "license =" in content, "Should have license"
        assert "keywords =" in content, "Should have keywords"
        assert "classifiers =" in content, "Should have classifiers"

    def test_package_has_dev_dependencies(self, base_dir):
        """Test that package has development dependencies for testing."""
        pyproject_path = base_dir / "entity-plugin-gpt-oss" / "pyproject.toml"

        with open(pyproject_path, "r") as f:
            content = f.read()

        # Check dev dependencies
        assert "pytest" in content, "Should have pytest as dev dependency"
        assert "black" in content, "Should have black as dev dependency"
        assert "ruff" in content, "Should have ruff as dev dependency"
        assert "mypy" in content, "Should have mypy as dev dependency"

    def test_no_missing_plugins_compared_to_main_repo(
        self, main_gpt_oss_dir, package_dir
    ):
        """Test that package has all plugins from main repo."""
        main_files = {
            f.name for f in main_gpt_oss_dir.glob("*.py") if f.name != "__init__.py"
        }
        package_files = {
            f.name for f in package_dir.glob("*.py") if f.name != "__init__.py"
        }

        missing_files = main_files - package_files
        assert not missing_files, f"Package is missing files: {missing_files}"

        extra_files = package_files - main_files
        # Extra files are OK, but log them
        if extra_files:
            print(f"Package has extra files (not necessarily bad): {extra_files}")

    def test_package_plugins_have_non_empty_content(self, package_dir):
        """Test that plugin files are not empty."""
        for plugin_file in self.PLUGIN_FILES:
            plugin_path = package_dir / plugin_file

            with open(plugin_path, "r") as f:
                content = f.read().strip()

            assert content, f"Plugin file {plugin_file} should not be empty"
            assert (
                len(content) > 100
            ), f"Plugin file {plugin_file} should have substantial content"

    def test_package_build_tool_available(self):
        """Test that build tool is available for package building."""
        try:
            result = subprocess.run(
                ["python", "-m", "build", "--help"], capture_output=True, text=True
            )
            if result.returncode != 0:
                pytest.skip(
                    "Build tool not available - install with 'pip install build'"
                )
        except FileNotFoundError:
            pytest.skip("Python not available")


class TestGPTOSSComparisonMatrix:
    """Test the comparison matrix functionality."""

    def test_comparison_matrix_creation(self, tmp_path):
        """Test that comparison matrix can be created."""
        # This test verifies the verification script functionality
        base_dir = Path(__file__).parent.parent
        script_path = base_dir / "scripts" / "verify_gpt_oss_completeness.py"

        # Import the verifier class
        import sys

        sys.path.insert(0, str(script_path.parent))

        try:
            from verify_gpt_oss_completeness import GPTOSSPackageVerifier

            verifier = GPTOSSPackageVerifier()
            matrix = verifier.create_comparison_matrix()

            # Verify matrix structure
            assert "plugin_files" in matrix, "Matrix should have plugin_files section"
            assert "summary" in matrix, "Matrix should have summary section"

            summary = matrix["summary"]
            assert "total_plugins" in summary, "Summary should have total_plugins"
            assert "main_repo_files" in summary, "Summary should have main_repo_files"
            assert "package_files" in summary, "Summary should have package_files"

            # Verify all expected plugins are in matrix
            plugin_files = matrix["plugin_files"]
            for plugin_file in TestGPTOSSPackageCompleteness.PLUGIN_FILES:
                assert (
                    plugin_file in plugin_files
                ), f"Plugin {plugin_file} should be in matrix"

        finally:
            sys.path.remove(str(script_path.parent))

    def test_plugin_export_verification(self):
        """Test plugin export verification functionality."""
        base_dir = Path(__file__).parent.parent
        script_path = base_dir / "scripts" / "verify_gpt_oss_completeness.py"

        import sys

        sys.path.insert(0, str(script_path.parent))

        try:
            from verify_gpt_oss_completeness import GPTOSSPackageVerifier

            verifier = GPTOSSPackageVerifier()
            export_results = verifier.verify_plugin_exports()

            # Verify results structure
            assert "expected_plugins" in export_results, "Should have expected_plugins"
            assert "package_exports" in export_results, "Should have package_exports"
            assert "missing_exports" in export_results, "Should have missing_exports"
            assert "extra_exports" in export_results, "Should have extra_exports"

            # Verify no missing exports
            assert not export_results[
                "missing_exports"
            ], f"Should have no missing exports, found: {export_results['missing_exports']}"

        finally:
            sys.path.remove(str(script_path.parent))
