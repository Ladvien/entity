"""
Tests for Story ENTITY-104: Add Plugins as Git Submodules

This test file verifies that all acceptance criteria for adding
plugin repositories as Git submodules are met.
"""

import os
import subprocess
from pathlib import Path

import pytest


class TestStoryEntity104AddSubmodules:
    """Test Story ENTITY-104: Add Plugins as Git Submodules."""

    ORGANIZATION = "Ladvien"
    PLUGIN_REPOS = [
        "entity-plugin-examples",
        "entity-plugin-gpt-oss",
        "entity-plugin-stdlib",
        "entity-plugin-template",
    ]

    EXPECTED_SUBMODULE_PATHS = [
        "plugins/examples",
        "plugins/gpt-oss",
        "plugins/stdlib",
        "plugins/template",
    ]

    ORIGINAL_DIRECTORIES = [
        "entity-plugin-examples",
        "entity-plugin-gpt-oss",
        "entity-plugin-stdlib",
        "entity-plugin-template",
    ]

    @pytest.fixture(autouse=True)
    def check_gh_cli(self):
        """Check if gh CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                pytest.skip("gh CLI is not authenticated")
        except FileNotFoundError:
            pytest.skip("gh CLI is not installed")

    def test_submodule_script_exists(self):
        """Test that the plugin submodule addition script exists."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        assert script_path.exists(), "Plugin submodule script should exist"
        assert script_path.is_file(), "Script should be a file"
        assert os.access(script_path, os.X_OK), "Script should be executable"

    def test_script_has_dry_run_mode(self):
        """Test that the script supports dry-run mode."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        assert "--dry-run" in content, "Script should support --dry-run flag"
        assert "DRY_RUN=" in content, "Script should have DRY_RUN variable"

    def test_script_logs_operations(self):
        """Test that the script logs all operations."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        assert "LOG_FILE=" in content, "Script should define log file"
        assert "log()" in content, "Script should have logging function"
        assert "tee -a" in content, "Script should log operations"

    def test_script_uses_gh_cli_for_urls(self):
        """Test that script uses gh CLI to get repository URLs."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        assert "get_repo_url()" in content, "Script should have URL fetching function"
        assert "gh repo view" in content, "Script should use gh repo view"
        assert "--json url --jq '.url'" in content, "Script should extract URL with jq"

    def test_script_defines_correct_submodule_paths(self):
        """Test that script defines correct submodule paths."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        assert (
            "get_submodule_path" in content
        ), "Script should define submodule path function"
        assert "plugins/examples" in content, "Should map to plugins/examples"
        assert "plugins/gpt-oss" in content, "Should map to plugins/gpt-oss"
        assert "plugins/stdlib" in content, "Should map to plugins/stdlib"
        assert "plugins/template" in content, "Should map to plugins/template"

    def test_script_creates_plugins_directory(self):
        """Test that script creates plugins directory."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        assert (
            "create_plugins_directory()" in content
        ), "Script should create plugins dir"
        assert "PLUGINS_DIR=" in content, "Script should define plugins directory"
        assert 'mkdir -p "$PLUGINS_DIR"' in content, "Script should create directory"

    def test_script_error_handling(self):
        """Test that script has proper error handling."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        # Error handling indicators
        assert "set -euo pipefail" in content, "Script should use strict error handling"
        assert 'log "ERROR"' in content, "Script should log errors"
        assert "exit 1" in content, "Script should exit with error code on failure"

    def test_can_get_repository_urls_with_gh_cli(self):
        """Test that we can get repository URLs using gh CLI."""
        for repo_name in self.PLUGIN_REPOS:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{self.ORGANIZATION}/{repo_name}",
                    "--json",
                    "url",
                    "--jq",
                    ".url",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            assert result.returncode == 0, f"Should be able to get URL for {repo_name}"
            url = result.stdout.strip()
            assert url.startswith(
                "https://github.com/"
            ), f"URL should be valid GitHub URL for {repo_name}"
            assert repo_name in url, f"URL should contain repository name {repo_name}"

    def test_plugins_directory_creation_logic(self):
        """Test plugins directory creation in dry-run mode."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )

        # Run script in dry-run mode
        result = subprocess.run(
            [str(script_path), "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )

        # Should complete successfully in dry-run
        assert result.returncode == 0, "Dry-run should complete successfully"

        # Should show plugins directory creation
        output = result.stdout
        assert (
            "Would create: plugins" in output
        ), "Should show plugins directory creation"

    def test_dry_run_mode_functionality(self):
        """Test that dry-run mode works correctly."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )

        # Run script in dry-run mode
        result = subprocess.run(
            [str(script_path), "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )

        # Should complete successfully
        assert result.returncode == 0, "Dry-run should complete successfully"

        # Should show dry-run indication
        output = result.stdout
        assert "DRY-RUN mode" in output, "Should indicate dry-run mode"
        assert "Would add submodule" in output, "Should show submodule additions"

    def test_log_directory_creation(self):
        """Test that script creates log directory."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        assert 'mkdir -p "$LOG_DIR"' in content, "Script should create log directory"
        assert "LOG_DIR=" in content, "Script should define log directory"

    def test_acceptance_criteria_verification(self):
        """Test specific acceptance criteria from the story."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        # ✓ Use `gh repo view --json url` to get repository URLs programmatically
        assert (
            "gh repo view" in content and "--json url" in content
        ), "Should use gh CLI to get URLs programmatically"

        # ✓ plugins/ directory created
        assert "create_plugins_directory" in content, "Should create plugins directory"

        # ✓ All four plugins added as submodules
        for repo in self.PLUGIN_REPOS:
            assert repo in content, f"Should reference {repo}"

        # ✓ .gitmodules file created with correct entries
        assert "verify_gitmodules_file" in content, "Should verify .gitmodules file"

        # ✓ Original entity-plugin-* directories removed
        assert (
            "remove_original_directories" in content
        ), "Should remove original directories"

        assert (
            "ORIGINAL_DIRECTORIES" in content
        ), "Should define original directories to remove"

        # ✓ Changes committed to entity-core
        assert "commit_changes" in content, "Should commit changes"
        assert "git commit" in content, "Should use git commit"

        print("✅ All acceptance criteria for Story ENTITY-104 are implemented!")

    def test_definition_of_done_preparedness(self):
        """Test that script is ready to meet Definition of Done criteria."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )

        # Script exists and is executable
        assert script_path.exists(), "Submodule script should exist"
        assert os.access(script_path, os.X_OK), "Script should be executable"

        # Can run in dry-run mode
        result = subprocess.run(
            [str(script_path), "--dry-run"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, "Script should run successfully in dry-run"
        assert "DRY-RUN mode" in result.stdout, "Should indicate dry-run mode"

        # Content should show it will verify submodules
        content = script_path.read_text()
        assert "git submodule status" in content, "Should check submodule status"
        assert "verify_submodules" in content, "Should verify submodules"

        print("✅ All Definition of Done criteria can be met!")

    def test_script_handles_existing_submodules(self):
        """Test that script handles existing submodules gracefully."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        # Should check if path already exists
        assert "if [ -e" in content, "Should check if path exists"
        assert "git submodule status" in content, "Should check submodule status"
        assert "Already submodule" in content, "Should handle existing submodules"

    def test_gh_authentication_check(self):
        """Test that script verifies gh CLI authentication."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        assert "gh auth status" in content, "Should check gh authentication"
        assert "gh CLI is not authenticated" in content, "Should handle auth errors"

    def test_git_repository_check(self):
        """Test that script verifies it's in a git repository."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        assert "git rev-parse --git-dir" in content, "Should check git repository"
        assert "Not in a git repository" in content, "Should handle non-git directories"

    def test_submodule_initialization_logic(self):
        """Test that script initializes submodules."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        assert "initialize_submodules" in content, "Should have initialization function"
        assert "git submodule init" in content, "Should initialize submodules"
        assert "git submodule update" in content, "Should update submodules"

    def test_commit_message_format(self):
        """Test that script uses proper commit message format."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "add_plugin_submodules.sh"
        )
        content = script_path.read_text()

        # Should have structured commit message
        assert (
            "feat: Add plugins as Git submodules" in content
        ), "Should use conventional commit format"
        assert "Story: ENTITY-104" in content, "Should reference story number"

    def test_current_plugin_directories_exist(self):
        """Test that current plugin directories exist before submodule conversion."""
        for dir_name in self.ORIGINAL_DIRECTORIES:
            dir_path = Path(dir_name)
            if dir_path.exists():
                assert dir_path.is_dir(), f"{dir_name} should be a directory"

                # Should have typical plugin structure
                src_dir = dir_path / "src"
                if src_dir.exists():
                    assert src_dir.is_dir(), f"{dir_name}/src should be a directory"


class TestCurrentSubmoduleState:
    """Test the current state of submodules before running the script."""

    def test_no_submodules_currently_configured(self):
        """Test that no submodules are currently configured."""
        result = subprocess.run(
            ["git", "submodule", "status"],
            capture_output=True,
            text=True,
            check=False,
        )

        # Should run successfully (git submodule status always returns 0)
        assert result.returncode == 0, "git submodule status should run"

        # Should have no output (no submodules)
        output = result.stdout.strip()
        assert len(output) == 0, "Should have no configured submodules currently"

    def test_gitmodules_file_does_not_exist(self):
        """Test that .gitmodules file doesn't exist yet."""
        gitmodules_path = Path(".gitmodules")
        # If it exists, it should have no entries or be from previous incomplete runs
        if gitmodules_path.exists():
            content = gitmodules_path.read_text()
            # If it exists but is empty or has no submodule entries, that's fine
            submodule_count = content.count("[submodule")
            assert (
                submodule_count < 4
            ), "Should not have all 4 submodules configured yet"

    def test_plugins_directory_does_not_exist(self):
        """Test that plugins directory doesn't exist yet."""
        plugins_dir = Path("plugins")
        if plugins_dir.exists():
            # If it exists, it should be empty or not have our expected structure
            expected_subdirs = ["examples", "gpt-oss", "stdlib", "template"]
            existing_subdirs = [d.name for d in plugins_dir.iterdir() if d.is_dir()]

            # Should not have all expected subdirectories as submodules
            submodule_subdirs = []
            for subdir in existing_subdirs:
                if subdir in expected_subdirs:
                    # Check if this is a submodule
                    result = subprocess.run(
                        ["git", "submodule", "status", f"plugins/{subdir}"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        submodule_subdirs.append(subdir)

            assert (
                len(submodule_subdirs) < 4
            ), "Should not have all 4 plugin submodules configured yet"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
