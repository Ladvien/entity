"""Tests for plugin submodule structure and compatibility."""

import warnings
from pathlib import Path


class TestPluginSubmoduleStructure:
    """Test that plugin submodule directories exist and are properly structured."""

    def test_plugin_directories_exist(self):
        """Test that all plugin directories exist."""
        base_path = Path(__file__).parent.parent

        # Check main plugin directories
        assert (base_path / "entity-plugin-examples").exists()
        assert (base_path / "entity-plugin-stdlib").exists()
        assert (base_path / "entity-plugin-gpt-oss").exists()

    def test_plugin_packages_structure(self):
        """Test that plugin packages have correct structure."""
        base_path = Path(__file__).parent.parent

        # Check entity-plugin-examples structure
        examples_path = base_path / "entity-plugin-examples"
        assert (examples_path / "pyproject.toml").exists()
        assert (examples_path / "src" / "entity_plugin_examples").exists()
        assert (
            examples_path / "src" / "entity_plugin_examples" / "__init__.py"
        ).exists()

        # Check entity-plugin-stdlib structure
        stdlib_path = base_path / "entity-plugin-stdlib"
        assert (stdlib_path / "pyproject.toml").exists()
        assert (stdlib_path / "src" / "entity_plugin_stdlib").exists()
        assert (stdlib_path / "src" / "entity_plugin_stdlib" / "__init__.py").exists()

        # Check entity-plugin-gpt-oss structure
        gpt_oss_path = base_path / "entity-plugin-gpt-oss"
        assert (gpt_oss_path / "pyproject.toml").exists()
        assert (gpt_oss_path / "src" / "entity_plugin_gpt_oss").exists()

    def test_compatibility_layers_exist(self):
        """Test that compatibility layers exist for migration."""
        base_path = Path(__file__).parent.parent

        # Check compatibility modules
        compat_path = base_path / "src" / "entity" / "plugins"
        assert (compat_path / "examples_compat.py").exists()
        assert (compat_path / "gpt_oss_compat.py").exists()

    def test_documentation_exists(self):
        """Test that submodule documentation exists."""
        base_path = Path(__file__).parent.parent

        # Check documentation
        assert (base_path / "docs" / "SUBMODULE_GUIDE.md").exists()


class TestPluginCompatibility:
    """Test backward compatibility for plugin imports."""

    def test_examples_plugin_deprecation_warning(self):
        """Test that importing from old path shows deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            try:
                # This import will trigger deprecation warning
                from entity.plugins.examples import __doc__  # noqa: F401

                # Check that a deprecation warning was raised
                assert len(w) >= 1
                assert any(
                    issubclass(warning.category, DeprecationWarning) for warning in w
                )
                assert any(
                    "deprecated" in str(warning.message).lower() for warning in w
                )
            except ImportError as e:
                # Expected when package not installed - verify error message is helpful
                assert "entity-plugin-examples" in str(e)
                assert "pip install" in str(e)

    def test_gpt_oss_compat_exists(self):
        """Test that GPT-OSS compatibility layer exists and works."""
        # Import the compatibility module
        from entity.plugins import gpt_oss_compat  # noqa: F401

        # Check that it has the expected attributes
        assert hasattr(gpt_oss_compat, "__all__")
        assert "ReasoningTracePlugin" in gpt_oss_compat.__all__

    def test_plugin_directories_not_submodules_yet(self):
        """Test that plugin directories are not yet Git submodules.

        This test documents the current state where directories exist but
        aren't actual Git submodules yet. This will change when they're
        converted to actual external repositories.
        """
        base_path = Path(__file__).parent.parent
        gitmodules_path = base_path / ".gitmodules"

        # Currently .gitmodules should not exist as we haven't set up actual submodules
        # This is the expected state for local development
        assert (
            not gitmodules_path.exists()
        ), "Git submodules should not be configured yet"


class TestPluginMigrationPath:
    """Test the migration path from old to new plugin structure."""

    def test_migration_documentation(self):
        """Test that migration instructions are documented."""
        base_path = Path(__file__).parent.parent
        guide_path = base_path / "docs" / "SUBMODULE_GUIDE.md"

        assert guide_path.exists()

        # Check that guide contains key sections
        content = guide_path.read_text()
        assert "Migration Path" in content
        assert "Deprecation Timeline" in content
        assert "entity-plugin-examples" in content
        assert "entity-plugin-stdlib" in content
        assert "entity-plugin-gpt-oss" in content

    def test_pyproject_configuration(self):
        """Test that plugin pyproject.toml files are properly configured."""
        base_path = Path(__file__).parent.parent

        # Check entity-plugin-examples configuration
        examples_pyproject = base_path / "entity-plugin-examples" / "pyproject.toml"
        if examples_pyproject.exists():
            content = examples_pyproject.read_text()
            assert "entity-plugin-examples" in content
            assert "version = " in content

        # Check entity-plugin-stdlib configuration
        stdlib_pyproject = base_path / "entity-plugin-stdlib" / "pyproject.toml"
        if stdlib_pyproject.exists():
            content = stdlib_pyproject.read_text()
            assert "entity-plugin-stdlib" in content
            assert "version = " in content
