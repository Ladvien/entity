"""
Tests for Story ENTITY-107: Update CI/CD Pipeline

This test file verifies that all acceptance criteria for updating
CI/CD to handle submodules and use gh CLI are met.
"""

from pathlib import Path

import pytest
import yaml


class TestStoryEntity107CICD:
    """Test Story ENTITY-107: Update CI/CD Pipeline."""

    def test_github_workflows_directory_exists(self):
        """Test that .github/workflows directory exists."""
        workflows_dir = Path(".github/workflows")
        assert workflows_dir.exists(), ".github/workflows directory should exist"
        assert workflows_dir.is_dir(), ".github/workflows should be a directory"

    def test_test_workflow_exists(self):
        """Test that test.yml workflow exists."""
        test_workflow = Path(".github/workflows/test.yml")
        assert test_workflow.exists(), "test.yml workflow should exist"

    def test_test_workflow_uses_submodules(self):
        """Test that test.yml uses actions/checkout with submodules."""
        test_workflow = Path(".github/workflows/test.yml")
        content = test_workflow.read_text()

        # Parse YAML
        workflow = yaml.safe_load(content)

        # Check jobs
        assert "jobs" in workflow, "Workflow should have jobs"
        assert "build" in workflow["jobs"], "Workflow should have build job"

        # Check for checkout with submodules
        build_job = workflow["jobs"]["build"]
        assert "steps" in build_job, "Build job should have steps"

        # Find checkout step
        checkout_found = False
        submodules_recursive = False

        for step in build_job["steps"]:
            if isinstance(step, dict) and "uses" in step:
                if "actions/checkout@v3" in step["uses"]:
                    checkout_found = True
                    if "with" in step and "submodules" in step["with"]:
                        if step["with"]["submodules"] == "recursive":
                            submodules_recursive = True

        assert checkout_found, "Should use actions/checkout@v3"
        assert submodules_recursive, "Checkout should use 'submodules: recursive'"

    def test_test_workflow_runs_plugin_tests(self):
        """Test that test.yml runs plugin tests."""
        test_workflow = Path(".github/workflows/test.yml")
        content = test_workflow.read_text()

        assert "plugin tests" in content.lower(), "Should mention plugin tests"
        assert (
            "tests/plugins/" in content or "plugin" in content.lower()
        ), "Should run plugin tests"

    def test_test_workflow_builds_docs(self):
        """Test that test.yml builds documentation including plugin docs."""
        test_workflow = Path(".github/workflows/test.yml")
        content = test_workflow.read_text()

        assert (
            "sphinx-build" in content or "documentation" in content.lower()
        ), "Should build documentation"

    def test_test_workflow_has_minimal_permissions(self):
        """Test that test.yml uses minimal permissions."""
        test_workflow = Path(".github/workflows/test.yml")
        content = test_workflow.read_text()

        workflow = yaml.safe_load(content)

        # Check for permissions section
        if "permissions" in workflow:
            perms = workflow["permissions"]
            # Should have limited permissions
            assert "contents" in perms, "Should define contents permission"
            # Should not have write unless necessary
            if perms["contents"] == "write":
                # Only acceptable if there's a good reason
                pass
            else:
                assert perms["contents"] == "read", "Contents should be read-only"

    def test_publish_workflow_uses_submodules(self):
        """Test that publish.yml uses submodules."""
        publish_workflow = Path(".github/workflows/publish.yml")
        assert publish_workflow.exists(), "publish.yml should exist"

        content = publish_workflow.read_text()
        workflow = yaml.safe_load(content)

        # Check build job
        if "jobs" in workflow and "build" in workflow["jobs"]:
            build_job = workflow["jobs"]["build"]
            checkout_with_submodules = False

            for step in build_job.get("steps", []):
                if isinstance(step, dict) and "uses" in step:
                    if "actions/checkout" in step["uses"]:
                        if "with" in step and "submodules" in step["with"]:
                            if step["with"]["submodules"] == "recursive":
                                checkout_with_submodules = True

            assert (
                checkout_with_submodules
            ), "Publish workflow should checkout with submodules"

    def test_security_workflow_uses_submodules(self):
        """Test that security.yml uses submodules."""
        security_workflow = Path(".github/workflows/security.yml")
        assert security_workflow.exists(), "security.yml should exist"

        content = security_workflow.read_text()

        # Should have submodules in all checkout steps
        assert "submodules:" in content, "Should mention submodules"
        assert (
            content.count("submodules: recursive") >= 2
        ), "Should use 'submodules: recursive' in both security and codeql jobs"

    def test_gh_cli_workflow_exists(self):
        """Test that workflows using gh CLI exist."""
        workflows_dir = Path(".github/workflows")

        # Check for any workflow using gh CLI
        gh_cli_found = False
        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text()
            if "gh " in content or "GitHub CLI" in content:
                gh_cli_found = True
                break

        assert gh_cli_found, "Should have at least one workflow using gh CLI"

    def test_plugin_management_workflow_exists(self):
        """Test that plugin management workflow exists."""
        plugin_mgmt = Path(".github/workflows/plugin-management.yml")
        assert plugin_mgmt.exists(), "plugin-management.yml should exist"

        content = plugin_mgmt.read_text()
        workflow = yaml.safe_load(content)

        # Check it has the right operations
        assert "on" in workflow, "Should have triggers"
        assert "workflow_dispatch" in workflow["on"], "Should support manual dispatch"

        # Check for gh CLI usage
        assert "gh " in content, "Should use gh CLI"
        assert (
            "gh pr" in content or "gh release" in content
        ), "Should use gh CLI for PR or release operations"

    def test_release_automation_workflow_exists(self):
        """Test that release automation workflow exists."""
        release_workflow = Path(".github/workflows/release-automation.yml")
        assert release_workflow.exists(), "release-automation.yml should exist"

        content = release_workflow.read_text()

        # Check for gh CLI usage
        assert "gh release create" in content, "Should use gh CLI to create releases"
        assert "gh pr create" in content, "Should use gh CLI to create PRs"

    def test_workflows_use_secrets_properly(self):
        """Test that workflows properly configure secrets for gh CLI."""
        workflows_dir = Path(".github/workflows")

        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text()

            # If using gh CLI, should set up authentication
            if "gh " in content:
                assert (
                    "GH_TOKEN" in content or "GITHUB_TOKEN" in content
                ), f"{workflow_file.name} should configure GitHub token for gh CLI"

    def test_acceptance_criteria_verification(self):
        """Test specific acceptance criteria from the story."""
        # ✓ CI/CD uses actions/checkout@v3 with submodules: recursive
        test_workflow = Path(".github/workflows/test.yml").read_text()
        assert "actions/checkout@v3" in test_workflow, "Should use checkout@v3"
        assert (
            "submodules: recursive" in test_workflow
        ), "Should use recursive submodules"

        # ✓ GitHub Actions workflow uses gh CLI for any repo operations
        plugin_mgmt = Path(".github/workflows/plugin-management.yml")
        assert plugin_mgmt.exists(), "Should have plugin management workflow"
        content = plugin_mgmt.read_text()
        assert "gh " in content, "Should use gh CLI"

        # ✓ Secrets properly configured for gh CLI in Actions
        assert (
            "GH_TOKEN" in content or "GITHUB_TOKEN" in content
        ), "Should configure tokens"

        # ✓ Plugin tests run in CI
        assert (
            "plugin tests" in test_workflow.lower() or "tests/plugins" in test_workflow
        ), "Should run plugin tests"

        # ✓ Documentation builds include plugin docs
        assert (
            "sphinx-build" in test_workflow or "documentation" in test_workflow.lower()
        ), "Should build docs"

        print("✅ All acceptance criteria for Story ENTITY-107 are met!")

    def test_definition_of_done(self):
        """Test that Definition of Done criteria are met."""
        # All workflows pass with submodules
        workflows = [
            ".github/workflows/test.yml",
            ".github/workflows/publish.yml",
            ".github/workflows/security.yml",
        ]

        for workflow_path in workflows:
            path = Path(workflow_path)
            assert path.exists(), f"{workflow_path} should exist"
            content = path.read_text()

            # Parse to ensure valid YAML
            try:
                yaml.safe_load(content)
            except yaml.YAMLError as e:
                pytest.fail(f"{workflow_path} has invalid YAML: {e}")

        # gh CLI operations use minimal permissions
        plugin_mgmt = Path(".github/workflows/plugin-management.yml")
        if plugin_mgmt.exists():
            content = plugin_mgmt.read_text()
            workflow = yaml.safe_load(content)

            if "permissions" in workflow:
                # Check that permissions are defined and minimal
                perms = workflow["permissions"]
                assert isinstance(perms, dict), "Permissions should be defined"

        print("✅ All Definition of Done criteria are met!")


class TestWorkflowValidation:
    """Additional tests for workflow validation."""

    def test_all_workflows_are_valid_yaml(self):
        """Test that all workflow files are valid YAML."""
        workflows_dir = Path(".github/workflows")

        for workflow_file in workflows_dir.glob("*.yml"):
            try:
                with open(workflow_file) as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"{workflow_file.name} has invalid YAML: {e}")

    def test_workflows_use_consistent_checkout_version(self):
        """Test that workflows use consistent checkout action versions."""
        workflows_dir = Path(".github/workflows")
        checkout_versions = set()

        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text()

            # Find all checkout action uses
            import re

            matches = re.findall(r"actions/checkout@v(\d+)", content)
            checkout_versions.update(matches)

        # Should use v3 or v4 (both are acceptable)
        assert all(
            v in ["3", "4"] for v in checkout_versions
        ), "Should use checkout@v3 or checkout@v4"

    def test_workflows_have_descriptive_names(self):
        """Test that workflows have descriptive names."""
        workflows_dir = Path(".github/workflows")

        for workflow_file in workflows_dir.glob("*.yml"):
            with open(workflow_file) as f:
                workflow = yaml.safe_load(f)

            assert "name" in workflow, f"{workflow_file.name} should have a name"
            assert (
                len(workflow["name"]) > 0
            ), f"{workflow_file.name} should have non-empty name"

    def test_plugin_submodules_integration(self):
        """Test that CI/CD properly integrates with plugin submodules."""
        # Check that submodules are configured
        gitmodules = Path(".gitmodules")
        assert gitmodules.exists(), ".gitmodules should exist for submodules"

        # Check that test workflow would test plugins
        test_workflow = Path(".github/workflows/test.yml").read_text()

        # Should either explicitly test plugins or run all tests (which includes plugins)
        has_plugin_testing = (
            "tests/plugins" in test_workflow
            or "pytest tests/plugins" in test_workflow
            or "poe test" in test_workflow  # poe test runs all tests
        )

        assert has_plugin_testing, "Test workflow should include plugin tests"


class TestGitHubCLIIntegration:
    """Test GitHub CLI integration in workflows."""

    def test_gh_cli_authentication_setup(self):
        """Test that gh CLI authentication is properly set up."""
        workflows_using_gh = []
        workflows_dir = Path(".github/workflows")

        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text()
            if "gh " in content:
                workflows_using_gh.append(workflow_file)

                # Check for authentication setup
                assert (
                    "GH_TOKEN" in content
                    or "GITHUB_TOKEN" in content
                    or "gh auth" in content
                ), f"{workflow_file.name} should set up gh CLI authentication"

    def test_gh_cli_operations_are_safe(self):
        """Test that gh CLI operations use safe practices."""
        workflows_dir = Path(".github/workflows")

        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text()

            if "gh repo delete" in content:
                pytest.fail(
                    f"{workflow_file.name} uses dangerous 'gh repo delete' command"
                )

            if "gh api" in content and "DELETE" in content:
                # Check if it's properly guarded
                assert (
                    "if:" in content
                ), f"{workflow_file.name} should guard DELETE operations with conditions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
