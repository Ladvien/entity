"""
Tests for Story ENTITY-109: Create Management Tooling

This test file verifies that all plugin management scripts are properly
implemented and meet the acceptance criteria.
"""

import os
import subprocess
from pathlib import Path

import pytest


class TestStoryEntity109ManagementTooling:
    """Test Story ENTITY-109: Create Management Tooling."""

    def test_plugin_update_all_script_exists(self):
        """Test that plugin_update_all.sh script exists."""
        script_path = Path("scripts/plugin_update_all.sh")
        assert script_path.exists(), "plugin_update_all.sh should exist"
        assert script_path.is_file(), "Should be a file"
        assert os.access(script_path, os.X_OK), "Should be executable"

    def test_plugin_check_versions_script_exists(self):
        """Test that plugin_check_versions.sh script exists."""
        script_path = Path("scripts/plugin_check_versions.sh")
        assert script_path.exists(), "plugin_check_versions.sh should exist"
        assert script_path.is_file(), "Should be a file"
        assert os.access(script_path, os.X_OK), "Should be executable"

    def test_plugin_create_new_script_exists(self):
        """Test that plugin_create_new.sh script exists."""
        script_path = Path("scripts/plugin_create_new.sh")
        assert script_path.exists(), "plugin_create_new.sh should exist"
        assert script_path.is_file(), "Should be a file"
        assert os.access(script_path, os.X_OK), "Should be executable"

    def test_plugin_list_prs_script_exists(self):
        """Test that plugin_list_prs.sh script exists."""
        script_path = Path("scripts/plugin_list_prs.sh")
        assert script_path.exists(), "plugin_list_prs.sh should exist"
        assert script_path.is_file(), "Should be a file"
        assert os.access(script_path, os.X_OK), "Should be executable"

    def test_update_script_uses_gh_cli(self):
        """Test that update script uses gh CLI."""
        script_path = Path("scripts/plugin_update_all.sh")
        content = script_path.read_text()

        assert "gh " in content, "Should use gh CLI"
        assert "gh auth status" in content, "Should check gh authentication"
        assert "command -v gh" in content, "Should check for gh installation"

    def test_check_versions_script_uses_gh_release_list(self):
        """Test that check versions script uses gh release list."""
        script_path = Path("scripts/plugin_check_versions.sh")
        content = script_path.read_text()

        assert "gh release list" in content, "Should use gh release list"
        assert "gh api" in content, "Should use gh api for additional info"
        assert "--repo" in content, "Should specify repository"

    def test_create_new_script_uses_gh_repo_commands(self):
        """Test that create new script uses gh repo create and clone."""
        script_path = Path("scripts/plugin_create_new.sh")
        content = script_path.read_text()

        assert "gh repo create" in content, "Should use gh repo create"
        assert "gh repo clone" in content, "Should use gh repo clone"
        assert "--template" in content, "Should use template flag"
        assert "entity-plugin-template" in content, "Should reference template repo"

    def test_list_prs_script_uses_gh_pr_list(self):
        """Test that list PRs script uses gh pr list."""
        script_path = Path("scripts/plugin_list_prs.sh")
        content = script_path.read_text()

        assert "gh pr list" in content, "Should use gh pr list"
        assert "--state" in content, "Should filter by state"
        assert "--json" in content, "Should request JSON output"
        assert "jq" in content, "Should parse JSON with jq"

    def test_all_scripts_have_help_option(self):
        """Test that all scripts have --help option."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()
            assert (
                "--help" in content or "-h" in content
            ), f"{script_path} should have help option"
            assert "Usage:" in content, f"{script_path} should have usage documentation"

    def test_all_scripts_handle_authentication(self):
        """Test that all scripts handle gh authentication gracefully."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()
            assert "gh auth status" in content, f"{script_path} should check gh auth"
            assert (
                "gh auth login" in content
            ), f"{script_path} should suggest auth login if needed"

    def test_all_scripts_check_prerequisites(self):
        """Test that all scripts check prerequisites."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()
            assert (
                "check_prerequisites" in content
            ), f"{script_path} should have prerequisites check"
            assert "command -v gh" in content, f"{script_path} should check for gh CLI"
            # Git check is required for most but not all scripts (e.g., list PRs might not need it)
            if "update" in script_path or "create" in script_path:
                assert (
                    "command -v git" in content
                ), f"{script_path} should check for git"

    def test_all_scripts_use_proper_error_handling(self):
        """Test that all scripts have proper error handling."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()
            assert "set -euo pipefail" in content, f"{script_path} should use safe mode"
            assert "error()" in content, f"{script_path} should have error function"
            assert "exit 1" in content, f"{script_path} should exit on errors"

    def test_all_scripts_have_colored_output(self):
        """Test that all scripts use colored output for better UX."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()
            assert "RED=" in content, f"{script_path} should define color codes"
            assert "GREEN=" in content, f"{script_path} should have success color"
            assert "NC=" in content, f"{script_path} should have no color reset"

    def test_plugin_repos_consistent_across_scripts(self):
        """Test that plugin repository list is consistent."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_list_prs.sh",
        ]

        expected_repos = [
            "entity-plugin-examples",
            "entity-plugin-gpt-oss",
            "entity-plugin-stdlib",
            "entity-plugin-template",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()
            for repo in expected_repos:
                assert repo in content, f"{script_path} should include {repo}"

    def test_readme_updated_with_management_commands(self):
        """Test that README.md has been updated with management commands."""
        readme_path = Path("README.md")
        assert readme_path.exists(), "README.md should exist"

        content = readme_path.read_text()

        # Check for Plugin Management section
        assert "Plugin Management" in content, "Should have Plugin Management section"

        # Check for script references
        assert "plugin_update_all.sh" in content, "Should document plugin_update_all.sh"
        assert (
            "plugin_check_versions.sh" in content
        ), "Should document plugin_check_versions.sh"
        assert "plugin_create_new.sh" in content, "Should document plugin_create_new.sh"
        assert "plugin_list_prs.sh" in content, "Should document plugin_list_prs.sh"

        # Check for usage examples
        assert "./scripts/plugin_update_all.sh" in content, "Should show usage example"
        assert "gh auth login" in content, "Should mention authentication"

    def test_acceptance_criteria_met(self):
        """Test that all acceptance criteria from the story are met."""
        # Script to update all plugins using gh CLI
        update_script = Path("scripts/plugin_update_all.sh")
        assert update_script.exists(), "Update script exists"
        content = update_script.read_text()
        assert "gh " in content, "Uses gh CLI"
        assert "update_plugin" in content, "Has update functionality"

        # Script to check plugin versions using gh release list
        check_script = Path("scripts/plugin_check_versions.sh")
        assert check_script.exists(), "Check versions script exists"
        content = check_script.read_text()
        assert "gh release list" in content, "Uses gh release list"

        # Script to create new plugin from template
        create_script = Path("scripts/plugin_create_new.sh")
        assert create_script.exists(), "Create new plugin script exists"
        content = create_script.read_text()
        assert "gh repo create" in content, "Uses gh repo create"
        assert "gh repo clone" in content, "Uses gh repo clone"

        # Script to list all plugin PRs
        list_script = Path("scripts/plugin_list_prs.sh")
        assert list_script.exists(), "List PRs script exists"
        content = list_script.read_text()
        assert "gh pr list" in content, "Uses gh pr list"

        # All scripts use gh CLI for GitHub operations
        for script in [update_script, check_script, create_script, list_script]:
            content = script.read_text()
            assert "gh " in content, f"{script.name} uses gh CLI"

    def test_definition_of_done_met(self):
        """Test that Definition of Done criteria are met."""
        # Management scripts created and documented
        scripts = [
            Path("scripts/plugin_update_all.sh"),
            Path("scripts/plugin_check_versions.sh"),
            Path("scripts/plugin_create_new.sh"),
            Path("scripts/plugin_list_prs.sh"),
        ]

        for script in scripts:
            assert script.exists(), f"{script.name} exists"
            assert os.access(script, os.X_OK), f"{script.name} is executable"

        # Scripts handle authentication gracefully
        for script in scripts:
            content = script.read_text()
            assert "gh auth status" in content, f"{script.name} checks authentication"
            assert (
                "error" in content.lower()
            ), f"{script.name} handles authentication errors"

        # README updated with management commands
        readme = Path("README.md")
        content = readme.read_text()
        assert "Plugin Management" in content, "README has Plugin Management section"
        for script in scripts:
            assert script.name in content, f"README documents {script.name}"

    def test_script_syntax_valid(self):
        """Test that all scripts have valid bash syntax."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)

            # Check shebang
            with open(path, "r") as f:
                first_line = f.readline().strip()
                assert (
                    first_line == "#!/bin/bash"
                ), f"{script_path} should have bash shebang"

            # Verify script syntax
            result = subprocess.run(
                ["bash", "-n", str(path)], capture_output=True, text=True
            )
            assert (
                result.returncode == 0
            ), f"{script_path} syntax check failed: {result.stderr}"

    def test_scripts_follow_naming_convention(self):
        """Test that scripts follow the plugin_*.sh naming convention."""
        plugin_scripts = list(Path("scripts").glob("plugin_*.sh"))

        expected_scripts = [
            "plugin_update_all.sh",
            "plugin_check_versions.sh",
            "plugin_create_new.sh",
            "plugin_list_prs.sh",
        ]

        for expected in expected_scripts:
            script_path = Path("scripts") / expected
            assert (
                script_path in plugin_scripts
            ), f"{expected} follows naming convention"

    def test_scripts_have_logging(self):
        """Test that scripts have proper logging functions."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()
            assert "log()" in content, f"{script_path} should have log function"
            assert "error()" in content, f"{script_path} should have error function"
            assert "warning()" in content, f"{script_path} should have warning function"
            assert "success()" in content, f"{script_path} should have success function"


class TestManagementScriptFunctionality:
    """Test the functionality of management scripts."""

    def test_update_script_handles_submodules(self):
        """Test that update script handles submodules correctly."""
        script_path = Path("scripts/plugin_update_all.sh")
        content = script_path.read_text()

        assert "git submodule" in content, "Should use git submodule commands"
        assert "git fetch" in content, "Should fetch latest changes"
        assert "git pull" in content, "Should pull updates"
        assert "git diff" in content, "Should check for local changes"

    def test_check_versions_compares_commits(self):
        """Test that check versions script compares commits."""
        script_path = Path("scripts/plugin_check_versions.sh")
        content = script_path.read_text()

        assert "git rev-parse" in content, "Should get commit hashes"
        assert "current_commit" in content, "Should track current commit"
        assert "latest_commit" in content, "Should get latest commit"
        assert "up to date" in content.lower(), "Should report update status"

    def test_create_script_validates_input(self):
        """Test that create script validates plugin names."""
        script_path = Path("scripts/plugin_create_new.sh")
        content = script_path.read_text()

        assert "validate_plugin_name" in content, "Should validate plugin names"
        assert "entity-plugin-" in content, "Should check naming convention"
        assert "[a-z0-9-]" in content, "Should validate character set"

    def test_list_prs_supports_filters(self):
        """Test that list PRs script supports various filters."""
        script_path = Path("scripts/plugin_list_prs.sh")
        content = script_path.read_text()

        assert "--state" in content, "Should support state filter"
        assert "--open" in content, "Should filter open PRs"
        assert "--closed" in content, "Should filter closed PRs"
        assert "--merged" in content, "Should filter merged PRs"
        assert "--all" in content, "Should show all PRs"


class TestScriptIntegration:
    """Test integration aspects of the management scripts."""

    def test_scripts_use_consistent_configuration(self):
        """Test that scripts share consistent configuration."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()

            # Check for consistent organization (scripts that interact with GitHub API)
            if (
                "gh api" in content
                or "gh repo" in content
                or "gh pr" in content
                or "gh release" in content
            ):
                assert (
                    'GITHUB_ORG="Ladvien"' in content or "Ladvien" in content
                ), f"{script_path} should reference correct GitHub org when using gh CLI"

            # Check for path handling - scripts should determine their location
            assert "dirname" in content, f"{script_path} should use dirname for paths"

    def test_scripts_are_self_contained(self):
        """Test that scripts are self-contained and don't require sourcing."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()

            # Check for sourcing other scripts - look for actual source commands
            # Ignore commented lines and string contents
            actual_source_lines = []
            for line in content.split("\n"):
                # Skip comments and strings containing source/dot patterns
                if line.strip().startswith("#"):
                    continue
                # Look for actual source or . commands at line start (with optional whitespace)
                if line.strip().startswith("source ") or line.strip().startswith(". "):
                    # Exclude obvious system files
                    if not any(
                        sys_file in line
                        for sys_file in ["bashrc", "profile", "bash_", "/dev/null"]
                    ):
                        actual_source_lines.append(line)

            # Scripts should not source other project scripts
            assert (
                len(actual_source_lines) == 0
            ), f"{script_path} sources other scripts: {actual_source_lines}"

    def test_scripts_handle_missing_dependencies(self):
        """Test that scripts handle missing dependencies gracefully."""
        scripts = [
            "scripts/plugin_update_all.sh",
            "scripts/plugin_check_versions.sh",
            "scripts/plugin_create_new.sh",
            "scripts/plugin_list_prs.sh",
        ]

        for script_path in scripts:
            path = Path(script_path)
            content = path.read_text()

            # Check for dependency checks
            assert "command -v" in content, f"{script_path} should check for commands"
            assert (
                "exit 1" in content
            ), f"{script_path} should exit on missing dependencies"
            assert (
                "https://cli.github.com" in content or "cli.github.com" in content
            ), f"{script_path} should provide installation guidance"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
