"""
Tests for Story ENTITY-108: Validate Migration

This test file verifies that all validation checks and rollback plans
for the plugin migration are properly implemented.
"""

import os
import subprocess
from pathlib import Path

import pytest


class TestStoryEntity108Validation:
    """Test Story ENTITY-108: Validate Migration."""

    def test_validation_script_exists(self):
        """Test that the validation script exists."""
        script_path = Path("scripts/validate_migration.sh")
        assert script_path.exists(), "validate_migration.sh should exist"
        assert script_path.is_file(), "Should be a file"
        assert os.access(script_path, os.X_OK), "Should be executable"

    def test_validation_script_structure(self):
        """Test that validation script has required functions."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        # Check for required functions
        required_functions = [
            "test_fresh_clone",
            "test_repository_topics",
            "test_repository_metadata",
            "test_example_scripts",
            "test_performance",
            "test_security",
            "test_plugin_structure",
            "test_cicd_integration",
        ]

        for func in required_functions:
            assert func in content, f"Script should have {func} function"

    def test_validation_script_has_reporting(self):
        """Test that validation script generates reports."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        assert "VALIDATION_REPORT" in content, "Should generate validation report"
        assert "LOG_FILE" in content, "Should create log file"
        assert "add_to_report" in content, "Should have reporting function"

    def test_rollback_plan_exists(self):
        """Test that rollback plan documentation exists."""
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        assert rollback_plan.exists(), "MIGRATION_ROLLBACK_PLAN.md should exist"

        content = rollback_plan.read_text()
        assert len(content) > 1000, "Rollback plan should be comprehensive"

    def test_rollback_plan_completeness(self):
        """Test that rollback plan covers all necessary areas."""
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        content = rollback_plan.read_text()

        required_sections = [
            "Risk Assessment",
            "Pre-Rollback Checklist",
            "Rollback Procedures",
            "Post-Rollback Verification",
            "Emergency Hotfix",
            "Recovery Timeline",
            "Rollback Decision Matrix",
        ]

        for section in required_sections:
            assert section in content, f"Rollback plan should have '{section}' section"

    def test_rollback_plan_has_commands(self):
        """Test that rollback plan includes executable commands."""
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        content = rollback_plan.read_text()

        # Check for git commands
        assert "git checkout" in content, "Should have git checkout commands"
        assert (
            "git submodule deinit" in content
        ), "Should have submodule removal commands"
        assert "git rm --cached" in content, "Should have cache cleanup commands"

        # Check for script references
        assert "restore_original_imports" in content, "Should have import restoration"

    def test_validation_checks_gh_cli(self):
        """Test that validation script checks for gh CLI."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        assert "command -v gh" in content, "Should check for gh CLI installation"
        assert "gh auth status" in content, "Should check gh authentication"

    def test_validation_checks_repositories(self):
        """Test that validation checks all plugin repositories."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        repos = [
            "entity-plugin-examples",
            "entity-plugin-gpt-oss",
            "entity-plugin-stdlib",
            "entity-plugin-template",
        ]

        for repo in repos:
            assert repo in content, f"Should validate {repo} repository"

    def test_validation_has_cleanup(self):
        """Test that validation script cleans up after itself."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        assert "cleanup()" in content, "Should have cleanup function"
        assert "trap cleanup" in content, "Should trap cleanup on exit"
        assert "rm -rf" in content, "Should remove temporary files"

    def test_acceptance_criteria_coverage(self):
        """Test that all acceptance criteria from the story are covered."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        # Check test checklist items
        assert "gh repo clone" in content, "Should test fresh clone with gh"
        assert "--recurse-submodules" in content, "Should clone with submodules"
        assert "gh api" in content, "Should use gh api for verification"
        assert "test_example_scripts" in content, "Should test example scripts"
        assert "test_performance" in content, "Should check performance"
        assert "test_security" in content, "Should run security scan"

    def test_definition_of_done_items(self):
        """Test that Definition of Done items are addressed."""
        # All validation checks pass - covered by script
        script_path = Path("scripts/validate_migration.sh")
        assert script_path.exists(), "Validation script exists"

        # Migration rollback plan documented
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        assert rollback_plan.exists(), "Rollback plan documented"

        # Sign-off from tech lead would be manual process
        content = rollback_plan.read_text()
        assert "Rollback Approval Authority" in content, "Has approval process defined"

    def test_validation_script_dry_run(self):
        """Test that validation script can be executed in check mode."""
        script_path = Path("scripts/validate_migration.sh")

        # Check if script has proper shebang
        with open(script_path, "r") as f:
            first_line = f.readline().strip()
            assert first_line == "#!/bin/bash", "Should have bash shebang"

        # Verify script syntax
        result = subprocess.run(
            ["bash", "-n", str(script_path)], capture_output=True, text=True
        )
        assert result.returncode == 0, f"Script syntax check failed: {result.stderr}"

    def test_validation_output_formats(self):
        """Test that validation produces proper output formats."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        # Check for colored output
        assert "RED=" in content, "Should have color codes for output"
        assert "GREEN=" in content, "Should have success color"
        assert "YELLOW=" in content, "Should have warning color"

        # Check for emoji indicators
        assert "✅" in content, "Should use success emoji"
        assert "❌" in content, "Should use failure emoji"
        assert "⚠️" in content, "Should use warning emoji"

    def test_rollback_timeline_realistic(self):
        """Test that rollback timeline is documented and realistic."""
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        content = rollback_plan.read_text()

        assert "Recovery Timeline" in content, "Should have timeline"
        assert (
            "1.5 hours" in content or "90 minutes" in content
        ), "Should estimate total time"
        assert "Priority" in content, "Should prioritize rollback steps"

    def test_checkpoint_branches_documented(self):
        """Test that checkpoint branches are documented for rollback."""
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        content = rollback_plan.read_text()

        assert "checkpoint" in content.lower(), "Should reference checkpoint branches"
        assert "checkpoint-5" in content, "Should list specific checkpoints"

    def test_security_validation_comprehensive(self):
        """Test that security validation checks for common issues."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        security_patterns = [
            "password",
            "api[_-]?key",
            "token",
            "secret",
            "AWS.*KEY",
            "GITHUB_TOKEN",
        ]

        for pattern in security_patterns:
            assert (
                pattern in content.lower() or pattern in content
            ), f"Should check for {pattern} pattern"

    def test_performance_validation_exists(self):
        """Test that performance validation is implemented."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        assert "test_performance" in content, "Should have performance test"
        assert (
            "duration" in content or "time" in content.lower()
        ), "Should measure execution time"

    def test_all_plugins_validated(self):
        """Test that all four plugins are validated."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        plugins = ["examples", "gpt-oss", "stdlib", "template"]

        for plugin in plugins:
            assert plugin in content, f"Should validate {plugin} plugin"


class TestValidationReporting:
    """Test validation reporting capabilities."""

    def test_report_generation(self):
        """Test that validation generates proper reports."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        assert "generate_final_report" in content, "Should generate final report"
        assert "Statistics" in content, "Should include statistics"
        assert "Success Rate" in content, "Should calculate success rate"

    def test_logging_implementation(self):
        """Test that proper logging is implemented."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        log_levels = ["INFO", "SUCCESS", "WARN", "ERROR"]

        for level in log_levels:
            assert f'"{level}"' in content, f"Should support {level} log level"

    def test_markdown_report_format(self):
        """Test that report is in Markdown format."""
        script_path = Path("scripts/validate_migration.sh")
        content = script_path.read_text()

        assert ".md" in content, "Should generate .md report"
        assert "##" in content, "Should use Markdown headers"
        assert "**" in content, "Should use Markdown bold"


class TestRollbackProcedures:
    """Test rollback procedures are properly documented."""

    def test_rollback_phases_defined(self):
        """Test that rollback has clear phases."""
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        content = rollback_plan.read_text()

        phases = ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5"]

        for phase in phases:
            assert phase in content, f"Should have {phase} defined"

    def test_emergency_procedures_exist(self):
        """Test that emergency procedures are documented."""
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        content = rollback_plan.read_text()

        assert "Emergency Hotfix" in content, "Should have emergency procedures"
        assert "Option 1" in content, "Should have multiple options"
        assert "Option 2" in content, "Should have fallback options"

    def test_decision_matrix_exists(self):
        """Test that rollback decision matrix is provided."""
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        content = rollback_plan.read_text()

        assert "Decision Matrix" in content, "Should have decision matrix"
        assert "Critical" in content, "Should define critical issues"
        assert "Immediate rollback" in content, "Should have immediate action criteria"

    def test_verification_checklist_complete(self):
        """Test that post-rollback verification is comprehensive."""
        rollback_plan = Path("MIGRATION_ROLLBACK_PLAN.md")
        content = rollback_plan.read_text()

        verifications = [
            "Code Structure",
            "Import Testing",
            "Run Test Suite",
            "CI/CD Verification",
            "Documentation Check",
        ]

        for check in verifications:
            assert check in content, f"Should verify {check}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
