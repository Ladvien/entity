"""
Tests for Story ENTITY-106: Update Documentation

This test file verifies that all acceptance criteria for updating
documentation to reflect new plugin structure and gh CLI workflow are met.
"""

from pathlib import Path

import pytest


class TestStoryEntity106Documentation:
    """Test Story ENTITY-106: Update Documentation."""

    def test_readme_includes_submodule_instructions(self):
        """Test that README includes submodule clone instructions."""
        readme_path = Path("README.md")
        assert readme_path.exists(), "README.md should exist"

        content = readme_path.read_text()

        # Check for submodule clone instructions
        assert (
            "git clone --recurse-submodules" in content
        ), "README should include submodule clone command"

        assert (
            "git submodule init" in content
        ), "README should include submodule init command"

        assert (
            "git submodule update" in content
        ), "README should include submodule update command"

        # Check that instructions are in the installation section
        assert (
            "From Source" in content and "submodules" in content
        ), "Submodule instructions should be in From Source section"

    def test_contributing_includes_gh_cli_setup(self):
        """Test that CONTRIBUTING.md includes gh CLI setup instructions."""
        contributing_path = Path("CONTRIBUTING.md")
        assert contributing_path.exists(), "CONTRIBUTING.md should exist"

        content = contributing_path.read_text()

        # Check for gh CLI in prerequisites
        assert (
            "GitHub CLI" in content or "gh" in content
        ), "CONTRIBUTING should mention GitHub CLI"

        # Check for gh CLI commands
        assert "gh repo fork" in content, "Should include gh repo fork command"
        assert "gh pr create" in content, "Should include gh pr create command"

        # Check for submodule instructions in setup
        assert (
            "--recurse-submodules" in content
        ), "Should include submodule clone instructions"

    def test_plugin_development_guide_exists(self):
        """Test that plugin development guide exists and is comprehensive."""
        plugin_guide_path = Path("PLUGIN_DEVELOPMENT.md")
        assert plugin_guide_path.exists(), "PLUGIN_DEVELOPMENT.md should exist"

        content = plugin_guide_path.read_text()

        # Check for essential sections
        required_sections = [
            "Overview",
            "Plugin Architecture",
            "Getting Started",
            "Contributing to Existing Plugins",
            "Creating New Plugins",
            "Plugin Best Practices",
            "Security Considerations",
        ]

        for section in required_sections:
            assert section in content, f"Plugin guide should have '{section}' section"

        # Check for gh CLI workflow
        assert "gh repo fork" in content, "Plugin guide should include gh repo fork"
        assert "gh pr create" in content, "Plugin guide should include gh pr create"
        assert "gh repo create" in content, "Plugin guide should include gh repo create"

        # Check for submodule workflow
        assert (
            "git submodule add" in content
        ), "Should explain adding plugins as submodules"
        assert "git submodule update" in content, "Should explain updating submodules"

    def test_contributing_includes_plugin_workflow(self):
        """Test that CONTRIBUTING.md explains plugin contribution process."""
        contributing_path = Path("CONTRIBUTING.md")
        content = contributing_path.read_text()

        # Check for plugin contribution section
        assert "Plugin Development" in content, "Should have Plugin Development section"

        assert (
            "Contributing to Existing Plugins" in content
        ), "Should explain contributing to existing plugins"

        # Check for workflow steps
        assert (
            "Fork the plugin repository" in content or "gh repo fork" in content
        ), "Should explain forking plugins"

        assert (
            "Submit a pull request" in content or "gh pr create" in content
        ), "Should explain creating PRs"

        # Check for plugin structure
        assert (
            "Plugin Repository Structure" in content or "entity-plugin-" in content
        ), "Should show plugin structure"

    def test_security_notes_about_pats(self):
        """Test that security notes about using fine-grained PATs are included."""
        # Check CONTRIBUTING.md
        contributing_path = Path("CONTRIBUTING.md")
        contributing_content = contributing_path.read_text()

        assert (
            "Personal Access Token" in contributing_content
            or "PAT" in contributing_content
        ), "CONTRIBUTING should mention PATs"

        assert (
            "fine-grained" in contributing_content
            or "Fine-grained" in contributing_content
        ), "Should recommend fine-grained PATs"

        # Check PLUGIN_DEVELOPMENT.md
        plugin_guide_path = Path("PLUGIN_DEVELOPMENT.md")
        if plugin_guide_path.exists():
            plugin_content = plugin_guide_path.read_text()

            assert (
                "Security Considerations" in plugin_content
            ), "Plugin guide should have security section"

            assert (
                "Personal Access Token" in plugin_content or "PAT" in plugin_content
            ), "Plugin guide should mention PATs"

            assert (
                "fine-grained" in plugin_content.lower()
            ), "Should recommend fine-grained PATs"

            # Check for security best practices
            assert (
                "Never commit" in plugin_content or "never commit" in plugin_content
            ), "Should warn against committing secrets"

    def test_no_references_to_old_plugin_locations(self):
        """Test that documentation doesn't reference old plugin locations."""
        docs_to_check = ["README.md", "CONTRIBUTING.md", "PLUGIN_DEVELOPMENT.md"]

        for doc_file in docs_to_check:
            path = Path(doc_file)
            if path.exists():
                content = path.read_text()

                # Old patterns that shouldn't exist (except in migration notes)
                # Allow mentions in migration/deprecation context
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "from entity.plugins.gpt_oss" in line:
                        # Check if it's in a migration/deprecation context
                        context = "\n".join(
                            lines[max(0, i - 2) : min(len(lines), i + 3)]
                        )
                        assert (
                            "deprecated" in context.lower()
                            or "migration" in context.lower()
                            or "old" in context.lower()
                        ), f"Found old import pattern in {doc_file} without migration context"

    def test_readme_mentions_plugin_packages(self):
        """Test that README mentions the modular plugin packages."""
        readme_path = Path("README.md")
        content = readme_path.read_text()

        # Should mention plugin packages section
        assert (
            "Plugin Packages" in content or "plugin packages" in content.lower()
        ), "README should have plugin packages section"

        # Should mention some specific plugins
        assert (
            "entity-plugin-gpt-oss" in content
        ), "Should mention gpt-oss plugin package"

        # Should mention that they're optional
        assert (
            "optional" in content.lower() or "Optional" in content
        ), "Should indicate plugins are optional"

    def test_documentation_consistency(self):
        """Test that documentation is consistent across files."""
        # Check that GitHub organization is consistent where appropriate
        # Note: CONTRIBUTING.md uses placeholder names for user forks

        # README should reference the main repo
        readme = Path("README.md").read_text()
        assert (
            "github.com/Ladvien/entity" in readme
        ), "README should reference main repo"

        # PLUGIN_DEVELOPMENT should reference plugin repos
        plugin_guide = Path("PLUGIN_DEVELOPMENT.md").read_text()
        assert (
            "Ladvien/entity-plugin" in plugin_guide
        ), "Plugin guide should reference plugin repos"

        # CONTRIBUTING should reference the org for plugin repos
        contributing = Path("CONTRIBUTING.md").read_text()
        assert (
            "gh repo fork Ladvien/entity-plugin" in contributing
        ), "CONTRIBUTING should reference org plugin repos"

    def test_acceptance_criteria_verification(self):
        """Test specific acceptance criteria from the story."""
        # ✓ README includes submodule clone instructions
        readme = Path("README.md").read_text()
        assert (
            "--recurse-submodules" in readme
        ), "README should have submodule instructions"

        # ✓ Developer setup guide includes gh CLI setup
        contributing = Path("CONTRIBUTING.md").read_text()
        assert "gh" in contributing, "Should mention gh CLI"

        # ✓ Plugin development guide updated with new workflow
        plugin_guide = Path("PLUGIN_DEVELOPMENT.md")
        assert plugin_guide.exists(), "Plugin development guide should exist"
        content = plugin_guide.read_text()
        assert "gh repo fork" in content, "Should use gh CLI workflow"

        # ✓ Contributing guide explains plugin contribution process
        assert (
            "Plugin Development" in contributing
        ), "Contributing should explain plugins"

        # ✓ Security notes about using fine-grained PATs included
        assert (
            "fine-grained" in contributing.lower() or "Fine-grained" in contributing
        ), "Should mention fine-grained PATs"

        print("✅ All acceptance criteria for Story ENTITY-106 are met!")

    def test_definition_of_done(self):
        """Test that Definition of Done criteria are met."""
        # All documentation reflects new structure
        readme = Path("README.md").read_text()
        contributing = Path("CONTRIBUTING.md").read_text()
        plugin_guide = Path("PLUGIN_DEVELOPMENT.md").read_text()

        # Check for submodule mentions
        assert "submodule" in readme.lower(), "README should mention submodules"
        assert (
            "submodule" in contributing.lower()
        ), "CONTRIBUTING should mention submodules"
        assert (
            "submodule" in plugin_guide.lower()
        ), "Plugin guide should mention submodules"

        # Check for gh CLI mentions
        assert (
            "gh " in contributing or "GitHub CLI" in contributing
        ), "CONTRIBUTING should mention gh CLI"
        assert "gh " in plugin_guide, "Plugin guide should have gh CLI commands"

        # No references to old plugin locations (except in migration context)
        # This is checked in test_no_references_to_old_plugin_locations

        print("✅ All Definition of Done criteria are met!")


class TestDocumentationCompleteness:
    """Additional tests for documentation completeness."""

    def test_all_required_documentation_files_exist(self):
        """Test that all required documentation files exist."""
        required_files = [
            "README.md",
            "CONTRIBUTING.md",
            "PLUGIN_DEVELOPMENT.md",
            "LICENSE",
        ]

        for file_path in required_files:
            path = Path(file_path)
            assert path.exists(), f"Required file {file_path} should exist"
            assert path.stat().st_size > 0, f"{file_path} should not be empty"

    def test_documentation_has_examples(self):
        """Test that documentation includes practical examples."""
        plugin_guide = Path("PLUGIN_DEVELOPMENT.md").read_text()

        # Should have code examples
        assert "```python" in plugin_guide, "Should have Python code examples"
        assert "```bash" in plugin_guide, "Should have bash command examples"

        # Should have example plugin implementation
        assert (
            "class" in plugin_guide and "Plugin" in plugin_guide
        ), "Should show plugin class example"

    def test_documentation_links_are_referenced(self):
        """Test that documentation files reference each other appropriately."""
        readme = Path("README.md").read_text()
        contributing = Path("CONTRIBUTING.md").read_text()

        # README should link to CONTRIBUTING
        assert (
            "CONTRIBUTING.md" in readme or "Contributing" in readme
        ), "README should reference contributing guide"

        # README should mention plugin development
        assert "plugin" in readme.lower(), "README should mention plugin development"

        # CONTRIBUTING should reference plugin guide
        if Path("PLUGIN_DEVELOPMENT.md").exists():
            assert (
                "PLUGIN_DEVELOPMENT.md" in contributing
                or "Plugin Development" in contributing
                or "plugin development" in contributing.lower()
            ), "CONTRIBUTING should reference plugin development"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
