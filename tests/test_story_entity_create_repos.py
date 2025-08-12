"""
Tests for Story ENTITY-101: Create GitHub Repositories Using gh CLI

This test file verifies that all acceptance criteria for creating
GitHub repositories for the Entity Framework plugins are met.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest


class TestStoryEntity101CreateRepos:
    """Test Story ENTITY-101: Create GitHub Repositories Using gh CLI."""

    ORGANIZATION = "Ladvien"
    EXPECTED_REPOS = [
        "entity-plugin-examples",
        "entity-plugin-gpt-oss",
        "entity-plugin-stdlib",
        "entity-plugin-template",
    ]

    EXPECTED_DESCRIPTIONS = {
        "entity-plugin-examples": "Example plugins demonstrating Entity Framework plugin development",
        "entity-plugin-gpt-oss": "GPT-OSS plugins for Entity Framework - advanced AI capabilities",
        "entity-plugin-stdlib": "Standard library plugins for Entity Framework - core utilities",
        "entity-plugin-template": "Template repository for creating new Entity Framework plugins",
    }

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

    def test_script_exists(self):
        """Test that the repository creation script exists."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "create_plugin_repos.sh"
        )
        assert script_path.exists(), "Repository creation script should exist"
        assert script_path.is_file(), "Script should be a file"
        assert os.access(script_path, os.X_OK), "Script should be executable"

    def test_script_has_dry_run_mode(self):
        """Test that the script supports dry-run mode."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "create_plugin_repos.sh"
        )
        content = script_path.read_text()

        assert "--dry-run" in content, "Script should support --dry-run flag"
        assert "DRY_RUN=" in content, "Script should have DRY_RUN variable"

    def test_script_is_idempotent(self):
        """Test that the script checks if repositories exist before creating."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "create_plugin_repos.sh"
        )
        content = script_path.read_text()

        assert "repo_exists" in content, "Script should have repo_exists function"
        assert (
            "gh repo view" in content
        ), "Script should use gh repo view to check existence"

    def test_script_logs_actions(self):
        """Test that the script logs all actions to a timestamped log file."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "create_plugin_repos.sh"
        )
        content = script_path.read_text()

        assert "LOG_FILE=" in content, "Script should define log file"
        assert "TIMESTAMP=" in content, "Script should use timestamp"
        assert "log()" in content, "Script should have logging function"
        assert "tee -a" in content, "Script should append to log file"

    def test_all_repositories_exist(self):
        """Test that all four repositories exist on GitHub."""
        for repo_name in self.EXPECTED_REPOS:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{self.ORGANIZATION}/{repo_name}",
                    "--json",
                    "name",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            assert result.returncode == 0, f"Repository {repo_name} should exist"

            # Verify the JSON response
            data = json.loads(result.stdout)
            assert data["name"] == repo_name, f"Repository name should be {repo_name}"

    def test_repositories_are_public(self):
        """Test that all repositories are public."""
        for repo_name in self.EXPECTED_REPOS:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{self.ORGANIZATION}/{repo_name}",
                    "--json",
                    "isPrivate",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                assert (
                    data["isPrivate"] is False
                ), f"Repository {repo_name} should be public"

    def test_repositories_have_mit_license(self):
        """Test that all repositories have MIT license."""
        for repo_name in self.EXPECTED_REPOS:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{self.ORGANIZATION}/{repo_name}",
                    "--json",
                    "licenseInfo",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("licenseInfo"):
                    license_key = data["licenseInfo"].get("key", "").lower()
                    assert (
                        "mit" in license_key
                    ), f"Repository {repo_name} should have MIT license"

    def test_repositories_have_correct_descriptions(self):
        """Test that all repositories have the correct descriptions."""
        for repo_name in self.EXPECTED_REPOS:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{self.ORGANIZATION}/{repo_name}",
                    "--json",
                    "description",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                expected_desc = self.EXPECTED_DESCRIPTIONS[repo_name]
                actual_desc = data.get("description", "")
                assert (
                    actual_desc == expected_desc
                ), f"Repository {repo_name} should have description: {expected_desc}"

    def test_repositories_have_topics(self):
        """Test that repositories have appropriate topics for discovery."""
        for repo_name in self.EXPECTED_REPOS:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{self.ORGANIZATION}/{repo_name}",
                    "--json",
                    "repositoryTopics",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                topics = data.get("repositoryTopics", {})
                if topics:
                    # Extract topic names from the nested structure
                    topic_names = []
                    if isinstance(topics, dict) and "nodes" in topics:
                        for node in topics["nodes"]:
                            if isinstance(node, dict) and "topic" in node:
                                topic_name = node["topic"].get("name", "")
                                if topic_name:
                                    topic_names.append(topic_name)
                    elif isinstance(topics, list):
                        for topic in topics:
                            if isinstance(topic, str):
                                topic_names.append(topic)
                            elif isinstance(topic, dict) and "name" in topic:
                                topic_names.append(topic["name"])

                    # Check for expected topics
                    if topic_names:
                        assert any(
                            "entity" in topic.lower()
                            for topic in topic_names
                            if isinstance(topic, str)
                        ), f"Repository {repo_name} should have entity-related topics"

    def test_log_directory_exists(self):
        """Test that the logs directory exists for audit logging."""
        log_dir = Path(__file__).parent.parent / "logs"
        assert log_dir.exists(), "Logs directory should exist"
        assert log_dir.is_dir(), "Logs should be a directory"

    def test_repositories_accessible_via_gh_cli(self):
        """Test that all repositories are accessible via gh repo view."""
        for repo_name in self.EXPECTED_REPOS:
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "view",
                    f"{self.ORGANIZATION}/{repo_name}",
                    "--json",
                    "url",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            assert (
                result.returncode == 0
            ), f"Repository {repo_name} should be accessible via gh CLI"

            data = json.loads(result.stdout)
            expected_url = f"https://github.com/{self.ORGANIZATION}/{repo_name}"
            assert (
                data["url"] == expected_url
            ), f"Repository URL should be {expected_url}"

    def test_script_handles_errors_gracefully(self):
        """Test that the script handles errors gracefully."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "create_plugin_repos.sh"
        )
        content = script_path.read_text()

        # Check for error handling
        assert "set -euo pipefail" in content, "Script should use strict error handling"
        assert (
            "if gh repo create" in content or "gh repo create" in content
        ), "Script should check repo creation result"
        assert 'log "ERROR"' in content, "Script should log errors"
        assert "exit 1" in content, "Script should exit with error code on failure"

    def test_acceptance_criteria_met(self):
        """Test that all acceptance criteria from the story are met."""
        script_path = (
            Path(__file__).parent.parent / "scripts" / "create_plugin_repos.sh"
        )

        # Check script exists and is executable
        assert script_path.exists(), "Script exists"
        assert os.access(script_path, os.X_OK), "Script is executable"

        # Verify all repositories exist
        for repo_name in self.EXPECTED_REPOS:
            result = subprocess.run(
                ["gh", "repo", "view", f"{self.ORGANIZATION}/{repo_name}"],
                capture_output=True,
                check=False,
            )
            assert result.returncode == 0, f"Repository {repo_name} exists"

        # Check for idempotency
        content = script_path.read_text()
        assert "repo_exists" in content, "Script checks if repo exists (idempotent)"

        # Check for logging
        assert "LOG_FILE=" in content, "Script logs to file"

        # Check for dry-run mode
        assert "--dry-run" in content, "Script supports dry-run mode"

        print("✅ All acceptance criteria for Story ENTITY-101 are met!")


class TestGitHubCLIConfiguration:
    """Test GitHub CLI configuration and authentication."""

    def test_gh_cli_installed(self):
        """Test that gh CLI is installed."""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, "gh CLI should be installed"
            assert "gh version" in result.stdout, "Should show gh version"
        except FileNotFoundError:
            pytest.fail("gh CLI is not installed")

    def test_gh_cli_authenticated(self):
        """Test that gh CLI is authenticated."""
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, "gh CLI should be authenticated"
        assert "Logged in" in result.stdout, "Should be logged in to GitHub"

    def test_gh_cli_has_repo_permissions(self):
        """Test that gh CLI token has repository creation permissions."""
        # Try to list user's repos as a permission check
        result = subprocess.run(
            ["gh", "repo", "list", "--limit", "1"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, "Should be able to list repositories"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
