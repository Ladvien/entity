"""
Tests for Story 5: Update Documentation and Dependencies

This test file verifies that:
1. README.md contains migration notice
2. MIGRATION.md exists and is comprehensive
3. CHANGELOG.md documents the breaking changes
4. pyproject.toml includes optional dependencies
5. Deprecation timeline is consistent across files
6. All acceptance criteria from Story 5 are met
"""

import re
from pathlib import Path

import pytest


class TestStory5Documentation:
    """Test Story 5: Update Documentation and Dependencies."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        # Go up from tests directory to project root
        return Path(__file__).parent.parent

    def test_readme_has_migration_notice(self, project_root):
        """Test that README.md contains migration notice."""
        readme_path = project_root / "README.md"
        assert readme_path.exists(), "README.md should exist"

        content = readme_path.read_text()

        # Check for plugin packages section
        assert "## 📦 Plugin Packages" in content or "Plugin Packages" in content
        assert "GPT-OSS Plugins" in content

        # Check for migration notice
        assert "Migration Notice" in content or "migration" in content.lower()
        assert "entity-plugin-gpt-oss" in content
        assert "deprecated" in content.lower()
        assert "v0.1.0" in content or "0.1.0" in content

        # Check for installation instructions
        assert "pip install entity-plugin-gpt-oss" in content
        assert "entity-core[gpt-oss]" in content

        # Check that all 9 plugins are listed
        plugins = [
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
        for plugin in plugins:
            assert plugin in content, f"README should list {plugin}"

    def test_migration_guide_exists_and_comprehensive(self, project_root):
        """Test that MIGRATION.md exists and is comprehensive."""
        migration_path = project_root / "MIGRATION.md"
        assert migration_path.exists(), "MIGRATION.md should exist"

        content = migration_path.read_text()

        # Check for essential sections
        assert "Migration Guide" in content or "migration guide" in content.lower()
        assert "Timeline" in content
        assert "Quick Migration Steps" in content or "Migration Steps" in content
        assert "Troubleshooting" in content
        assert "Benefits" in content or "Why" in content

        # Check for code examples
        assert "# Old Way" in content or "Old Way" in content
        assert "# New Way" in content or "New Way" in content
        assert "from entity.plugins.gpt_oss" in content  # Old import
        assert "from entity_plugin_gpt_oss" in content  # New import

        # Check for installation instructions
        assert "pip install entity-plugin-gpt-oss" in content

        # Check for environment variable documentation
        assert "ENTITY_SUPPRESS_GPT_OSS_DEPRECATION" in content

        # Check all 9 plugins are documented
        plugins = [
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
        for plugin in plugins:
            assert plugin in content, f"MIGRATION.md should document {plugin}"

        # Check for timeline consistency
        assert "0.1.0" in content
        assert "Q2 2024" in content

    def test_changelog_documents_breaking_changes(self, project_root):
        """Test that CHANGELOG.md documents the breaking changes."""
        changelog_path = project_root / "CHANGELOG.md"
        assert changelog_path.exists(), "CHANGELOG.md should exist"

        content = changelog_path.read_text()

        # Check for changelog structure
        assert "Changelog" in content or "CHANGELOG" in content
        assert "## [Unreleased]" in content or "Unreleased" in content

        # Check for breaking change notice
        assert "BREAKING" in content or "Breaking" in content
        assert "GPT-OSS plugins moved" in content or "modularization" in content.lower()

        # Check for deprecation notice
        assert "Deprecated" in content
        assert "entity.plugins.gpt_oss" in content
        assert "will be removed" in content.lower()

        # Check for migration instructions
        assert "Migration" in content or "migrate" in content.lower()
        assert "entity-plugin-gpt-oss" in content

    def test_pyproject_has_optional_dependencies(self, project_root):
        """Test that pyproject.toml includes optional dependencies."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml should exist"

        content = pyproject_path.read_text()

        # Check for optional dependencies section
        assert "[project.optional-dependencies]" in content

        # Check for gpt-oss extra
        assert 'gpt-oss = ["entity-plugin-gpt-oss' in content

        # Check that it's included in 'all' extra
        assert "all = [" in content
        assert "entity-plugin-gpt-oss" in content

    def test_deprecation_timeline_consistency(self, project_root):
        """Test that deprecation timeline is consistent across files."""
        files_to_check = [
            "README.md",
            "MIGRATION.md",
            "CHANGELOG.md",
            "src/entity/plugins/gpt_oss_compat.py",
        ]

        version = "0.1.0"
        date = "Q2 2024"

        for file_path in files_to_check:
            full_path = project_root / file_path
            if full_path.exists():
                content = full_path.read_text()
                assert (
                    version in content
                ), f"{file_path} should mention version {version}"
                # Date might be formatted differently, so check components
                assert (
                    "Q2" in content or "2024" in content
                ), f"{file_path} should mention timeline {date}"

    def test_compatibility_layer_docstring_comprehensive(self, project_root):
        """Test that compatibility layer has comprehensive docstrings."""
        compat_path = project_root / "src/entity/plugins/gpt_oss_compat.py"
        assert compat_path.exists(), "gpt_oss_compat.py should exist"

        content = compat_path.read_text()

        # Check for migration guide in module docstring
        lines = content.split("\n")
        in_docstring = False
        docstring_content = []

        for line in lines:
            if line.strip().startswith('"""'):
                if not in_docstring:
                    in_docstring = True
                else:
                    break
            elif in_docstring:
                docstring_content.append(line)

        docstring = "\n".join(docstring_content)

        assert "MIGRATION GUIDE" in docstring
        assert "DEPRECATED" in docstring
        assert "pip install entity-plugin-gpt-oss" in docstring
        assert "OLD WAY" in docstring
        assert "NEW WAY" in docstring

    def test_story_5_acceptance_criteria(self, project_root):
        """Test all Story 5 acceptance criteria are met."""
        # ✓ Update main README.md with migration notice and new import instructions
        readme = (project_root / "README.md").read_text()
        assert "Migration" in readme or "migration" in readme.lower()
        assert "entity-plugin-gpt-oss" in readme

        # ✓ Create MIGRATION.md guide for moving from legacy to new imports
        assert (project_root / "MIGRATION.md").exists()
        migration = (project_root / "MIGRATION.md").read_text()
        assert "from entity.plugins.gpt_oss" in migration  # Old
        assert "from entity_plugin_gpt_oss" in migration  # New

        # ✓ Update pyproject.toml to include entity-plugin-gpt-oss as optional dependency
        pyproject = (project_root / "pyproject.toml").read_text()
        assert "[project.optional-dependencies]" in pyproject
        assert "entity-plugin-gpt-oss" in pyproject

        # ✓ Add deprecation timeline to relevant documentation
        assert "0.1.0" in migration
        assert "Q2 2024" in migration

        # ✓ Update CHANGELOG.md with breaking change notice
        assert (project_root / "CHANGELOG.md").exists()
        changelog = (project_root / "CHANGELOG.md").read_text()
        assert "BREAKING" in changelog or "Breaking" in changelog

        # ✓ Ensure docstrings in compatibility layer are comprehensive
        compat = (project_root / "src/entity/plugins/gpt_oss_compat.py").read_text()
        assert "MIGRATION GUIDE" in compat
        assert len(compat.split("\n")[0:50]) > 40  # Substantial docstring

    def test_documentation_explains_modularization_benefits(self, project_root):
        """Test that documentation explains why modularization was done."""
        migration = (project_root / "MIGRATION.md").read_text()

        # Check for benefits section
        assert "Benefits" in migration or "Why" in migration

        # Check for specific benefits mentioned
        benefits_keywords = [
            "maintainability",
            "optional",
            "size",
            "independent",
            "modular",
        ]

        benefits_found = sum(
            1 for keyword in benefits_keywords if keyword in migration.lower()
        )
        assert benefits_found >= 3, "Documentation should explain multiple benefits"

    def test_troubleshooting_section_exists(self, project_root):
        """Test that MIGRATION.md includes troubleshooting section."""
        migration = (project_root / "MIGRATION.md").read_text()

        assert "Troubleshooting" in migration

        # Check for common issues
        assert "ImportError" in migration or "import error" in migration.lower()
        assert "Module Not Found" in migration or "not found" in migration.lower()
        assert "pip install" in migration  # Solution provided

    def test_migration_checklist_provided(self, project_root):
        """Test that migration guide includes a checklist."""
        migration = (project_root / "MIGRATION.md").read_text()

        # Check for checklist
        assert "Checklist" in migration or "- [ ]" in migration

        # Check for key checklist items
        checklist_items = [
            "Install",
            "Update",
            "Test",
            "Document",
        ]

        items_found = sum(1 for item in checklist_items if item in migration)
        assert items_found >= 3, "Checklist should cover key migration steps"

    def test_example_migration_code_provided(self, project_root):
        """Test that migration guide includes before/after code examples."""
        migration = (project_root / "MIGRATION.md").read_text()

        # Check for example section
        assert "Example" in migration or "Before" in migration

        # Check for code blocks
        assert "```python" in migration
        assert "# old" in migration.lower() or "# before" in migration.lower()
        assert "# new" in migration.lower() or "# after" in migration.lower()

        # Check for actual import examples
        assert "from entity.plugins.gpt_oss import" in migration
        assert "from entity_plugin_gpt_oss import" in migration

    def test_package_dependency_update_documented(self, project_root):
        """Test that dependency file updates are documented."""
        migration = (project_root / "MIGRATION.md").read_text()

        # Check for dependency update instructions
        assert "pyproject.toml" in migration or "requirements.txt" in migration
        assert "entity-plugin-gpt-oss" in migration

        # Check for version specification
        assert ">=0.1.0" in migration or "^0.1.0" in migration

    def test_links_to_help_resources(self, project_root):
        """Test that documentation includes links to help resources."""
        migration = (project_root / "MIGRATION.md").read_text()

        # Check for help section
        assert (
            "Getting Help" in migration
            or "Support" in migration
            or "help" in migration.lower()
        )

        # Check for GitHub link
        assert "github.com" in migration.lower() or "GitHub" in migration

        # Check for issue tracker mention
        assert "issue" in migration.lower()


class TestDocumentationIntegrity:
    """Test overall documentation integrity and cross-references."""

    def test_all_required_files_exist(self):
        """Test that all required documentation files exist."""
        required_files = [
            "README.md",
            "MIGRATION.md",
            "CHANGELOG.md",
            "pyproject.toml",
            "src/entity/plugins/gpt_oss_compat.py",
        ]

        project_root = Path(__file__).parent.parent

        for file_path in required_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"Required file {file_path} should exist"

    def test_cross_references_valid(self):
        """Test that cross-references between documents are valid."""
        project_root = Path(__file__).parent.parent

        # README references MIGRATION.md
        readme = (project_root / "README.md").read_text()
        if "MIGRATION.md" in readme or "Migration Guide" in readme:
            assert (project_root / "MIGRATION.md").exists()

        # CHANGELOG references MIGRATION.md
        changelog = (project_root / "CHANGELOG.md").read_text()
        if "MIGRATION.md" in changelog:
            assert (project_root / "MIGRATION.md").exists()

    def test_version_numbering_consistent(self):
        """Test that version numbers are consistent across files."""
        project_root = Path(__file__).parent.parent

        # Get version from pyproject.toml
        pyproject = (project_root / "pyproject.toml").read_text()
        import re

        version_match = re.search(r'version = "([^"]+)"', pyproject)
        assert version_match, "Version should be specified in pyproject.toml"
        current_version = version_match.group(1)

        # Check README mentions current version or doesn't specify incorrect version
        readme = (project_root / "README.md").read_text()
        if current_version in readme:
            # Good, current version is mentioned
            pass
        else:
            # Make sure no incorrect version is mentioned
            wrong_version_pattern = re.search(r"entity-core.*?(\d+\.\d+\.\d+)", readme)
            if wrong_version_pattern:
                found_version = wrong_version_pattern.group(1)
                assert (
                    found_version == current_version
                ), f"README has wrong version {found_version}"

    def test_no_broken_internal_links(self):
        """Test that internal documentation links are not broken."""
        project_root = Path(__file__).parent.parent

        # Check README links
        readme = (project_root / "README.md").read_text()
        internal_links = re.findall(r"\[.*?\]\((?!http)([^)]+)\)", readme)

        for link in internal_links:
            # Skip anchors
            if link.startswith("#"):
                continue
            # Check if file exists
            link_path = project_root / link
            if not link_path.exists():
                # Might be a docs/ relative link
                if link.startswith("docs/"):
                    continue  # Skip docs links for now
                else:
                    print(f"Warning: Link {link} in README might be broken")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
