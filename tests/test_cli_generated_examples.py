"""Test that CLI-generated examples work correctly."""

import ast
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Add src to path to avoid dependency issues
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCLIGeneratedExamples:
    """Test suite for validating CLI-generated project examples."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory for test projects."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def create_test_project(
        self,
        temp_dir: Path,
        project_name: str = "test_project",
        template: str = "basic",
    ) -> Path:
        """Create a test project using the CLI init command."""
        from entity.cli.commands.init import (
            create_env_example,
            create_project_structure,
        )

        project_path = temp_dir / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        create_project_structure(project_path, template)
        create_env_example(project_path, "ollama")

        return project_path

    def test_generated_main_py_syntax_valid(self, temp_project_dir):
        """Test that generated main.py has valid Python syntax."""
        project_path = self.create_test_project(temp_project_dir)
        main_file = project_path / "main.py"

        assert main_file.exists(), "main.py should be created"

        # Test syntax by parsing
        with main_file.open() as f:
            content = f.read()

        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Generated main.py has syntax error: {e}")

    def test_generated_main_py_imports(self, temp_project_dir):
        """Test that generated main.py imports are correct."""
        project_path = self.create_test_project(temp_project_dir)
        main_file = project_path / "main.py"

        content = main_file.read_text()

        # Check for correct imports
        assert "from entity import Agent" in content, "Should import Agent correctly"
        assert (
            "from entity.defaults import load_defaults" in content
        ), "Should import load_defaults"
        assert "import asyncio" in content, "Should import asyncio"
        assert "import sys" in content, "Should import sys"

        # Check for proper patterns
        assert "asyncio.run(main_async())" in content, "Should use asyncio.run pattern"
        assert "except KeyboardInterrupt:" in content, "Should handle KeyboardInterrupt"
        assert "load_defaults()" in content, "Should call load_defaults()"

    def test_generated_workflow_yaml_valid(self, temp_project_dir):
        """Test that generated workflow YAML is valid."""
        project_path = self.create_test_project(temp_project_dir)
        workflow_file = project_path / "workflows" / "basic.yaml"

        assert workflow_file.exists(), "basic.yaml workflow should be created"

        # Test YAML syntax
        try:
            with workflow_file.open() as f:
                workflow_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Generated workflow YAML is invalid: {e}")

        # Check workflow structure
        assert isinstance(workflow_data, dict), "Workflow should be a dictionary"

        # Check required stages exist
        required_stages = ["input", "parse", "think", "output"]
        for stage in required_stages:
            assert stage in workflow_data, f"Workflow should have {stage} stage"
            assert isinstance(
                workflow_data[stage], list
            ), f"{stage} should be a list of plugins"
            assert (
                len(workflow_data[stage]) > 0
            ), f"{stage} should have at least one plugin"

    def test_generated_workflow_plugins_exist(self, temp_project_dir):
        """Test that referenced plugins actually exist in the framework."""
        project_path = self.create_test_project(temp_project_dir)
        workflow_file = project_path / "workflows" / "basic.yaml"

        with workflow_file.open() as f:
            workflow_data = yaml.safe_load(f)

        # Extract all plugin references
        plugin_references = []
        for stage, plugins in workflow_data.items():
            if isinstance(plugins, list):
                for plugin in plugins:
                    if isinstance(plugin, str) and not plugin.startswith("#"):
                        plugin_references.append(plugin)

        # Test that plugin modules can be imported (at least the module part)
        for plugin_ref in plugin_references:
            if "." in plugin_ref:
                module_path = ".".join(plugin_ref.split(".")[:-1])
                try:
                    # Try to import the module
                    parts = module_path.split(".")
                    if parts[0] == "entity":
                        # This is a framework plugin, should be importable
                        # We'll check if the module exists in the codebase
                        module_file_path = Path(__file__).parent.parent / "src"
                        for part in parts:
                            module_file_path = module_file_path / part

                        # Check if either __init__.py or the module.py exists
                        init_file = module_file_path / "__init__.py"
                        py_file = module_file_path.with_suffix(".py")

                        assert (
                            init_file.exists() or py_file.exists()
                        ), f"Plugin module {module_path} should exist in framework"
                except Exception as e:
                    pytest.fail(
                        f"Plugin reference {plugin_ref} points to non-existent module: {e}"
                    )

    def test_generated_test_file_syntax_valid(self, temp_project_dir):
        """Test that generated test file has valid Python syntax."""
        project_path = self.create_test_project(temp_project_dir)
        test_file = project_path / "tests" / "test_test_project.py"

        assert test_file.exists(), "Test file should be created"

        # Test syntax
        content = test_file.read_text()
        try:
            ast.parse(content)
        except SyntaxError as e:
            pytest.fail(f"Generated test file has syntax error: {e}")

    def test_generated_test_file_structure(self, temp_project_dir):
        """Test that generated test file has correct structure."""
        project_path = self.create_test_project(temp_project_dir)
        test_file = project_path / "tests" / "test_test_project.py"

        content = test_file.read_text()

        # Check imports
        assert "import pytest" in content, "Should import pytest"
        assert "from entity import Agent" in content, "Should import Agent correctly"
        assert (
            "from entity.defaults import load_defaults" in content
        ), "Should import load_defaults"

        # Check test function structure
        assert "@pytest.mark.asyncio" in content, "Should have async test markers"
        assert "async def test_" in content, "Should have async test functions"
        assert (
            "pytest.skip(" in content
        ), "Should handle missing infrastructure gracefully"

    def test_env_example_file_created(self, temp_project_dir):
        """Test that .env.example file is created with correct content."""
        project_path = self.create_test_project(temp_project_dir)
        env_file = project_path / ".env.example"

        assert env_file.exists(), ".env.example should be created"

        content = env_file.read_text()

        # Check for essential environment variables
        assert "DB_HOST=" in content, "Should include database config"
        assert "LOG_LEVEL=" in content, "Should include logging config"
        assert (
            "OLLAMA_BASE_URL=" in content
        ), "Should include LLM config for selected service"

    def test_directory_structure_complete(self, temp_project_dir):
        """Test that all expected directories are created."""
        project_path = self.create_test_project(temp_project_dir)

        expected_dirs = ["src", "tests", "data", "workflows", "plugins"]

        for dir_name in expected_dirs:
            dir_path = project_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} should be created"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"

    def test_readme_content_accurate(self, temp_project_dir):
        """Test that README contains accurate project information."""
        project_name = "my_test_agent"
        project_path = self.create_test_project(temp_project_dir, project_name)
        readme_file = project_path / "README.md"

        assert readme_file.exists(), "README.md should be created"

        content = readme_file.read_text()

        # Check project name is included
        assert project_name in content, "README should contain project name"

        # Check Entity framework concepts
        assert (
            "Agent = Resources + Workflow + Infrastructure" in content
        ), "Should explain Entity mental model"
        assert "4-layer architecture" in content, "Should explain architecture"
        assert "6 stages" in content, "Should explain workflow stages"

        # Check practical information
        assert "python main.py" in content, "Should include run instructions"
        assert "cp .env.example .env" in content, "Should include setup instructions"
        assert "entity-core.readthedocs.io" in content, "Should link to documentation"

    @pytest.mark.integration
    def test_generated_project_can_run_syntax_check(self, temp_project_dir):
        """Integration test: generated project passes Python syntax check."""
        project_path = self.create_test_project(temp_project_dir)
        main_file = project_path / "main.py"

        # Run Python syntax check
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(main_file)],
            capture_output=True,
            text=True,
        )

        assert (
            result.returncode == 0
        ), f"main.py should compile without errors: {result.stderr}"

    def test_different_llm_services_env_configs(self, temp_project_dir):
        """Test that different LLM service selections generate correct env configs."""
        from entity.cli.commands.init import create_env_example

        project_path = temp_project_dir / "test_llm_configs"
        project_path.mkdir()

        # Test different LLM service configurations
        llm_services = ["ollama", "openai", "anthropic", "gemini"]

        for service in llm_services:
            create_env_example(project_path, service)
            env_content = (project_path / ".env.example").read_text()

            if service == "ollama":
                assert "OLLAMA_BASE_URL=" in env_content
                assert "OLLAMA_MODEL=" in env_content
            elif service == "openai":
                assert "OPENAI_API_KEY=" in env_content
                assert "OPENAI_MODEL=" in env_content
            elif service == "anthropic":
                assert "ANTHROPIC_API_KEY=" in env_content
                assert "ANTHROPIC_MODEL=" in env_content
            elif service == "gemini":
                assert "GOOGLE_API_KEY=" in env_content
                assert "GEMINI_MODEL=" in env_content

    def test_workflow_template_consistency(self, temp_project_dir):
        """Test that workflow templates are consistent with framework patterns."""
        project_path = self.create_test_project(temp_project_dir)
        workflow_file = project_path / "workflows" / "basic.yaml"

        with workflow_file.open() as f:
            workflow_data = yaml.safe_load(f)

        # Check that plugin references follow framework conventions
        for stage, plugins in workflow_data.items():
            if isinstance(plugins, list):
                for plugin in plugins:
                    if isinstance(plugin, str) and "entity.plugins" in plugin:
                        # Should follow entity.plugins.category.PluginName pattern
                        parts = plugin.split(".")
                        assert (
                            len(parts) >= 4
                        ), f"Plugin {plugin} should follow naming convention"
                        assert (
                            parts[0] == "entity"
                        ), f"Plugin {plugin} should start with 'entity'"
                        assert (
                            parts[1] == "plugins"
                        ), f"Plugin {plugin} should be in plugins namespace"

    @pytest.mark.slow
    def test_full_project_creation_workflow(self, temp_project_dir):
        """Full integration test of the project creation workflow."""
        project_name = "full_test_project"

        # Create project
        project_path = self.create_test_project(temp_project_dir, project_name, "basic")

        # Verify all expected files exist
        expected_files = [
            "main.py",
            "README.md",
            ".env.example",
            "workflows/basic.yaml",
            f"tests/test_{project_name}.py",
        ]

        for file_path in expected_files:
            full_path = project_path / file_path
            assert full_path.exists(), f"File {file_path} should exist"
            assert full_path.stat().st_size > 0, f"File {file_path} should not be empty"

        # Verify Python files have valid syntax
        python_files = [
            project_path / "main.py",
            project_path / "tests" / f"test_{project_name}.py",
        ]

        for py_file in python_files:
            try:
                with py_file.open() as f:
                    ast.parse(f.read())
            except SyntaxError as e:
                pytest.fail(f"File {py_file} has syntax error: {e}")

        # Verify YAML files are valid
        yaml_files = [project_path / "workflows" / "basic.yaml"]

        for yaml_file in yaml_files:
            try:
                with yaml_file.open() as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"File {yaml_file} has YAML error: {e}")


if __name__ == "__main__":
    # Run tests directly for development
    pytest.main([__file__, "-v"])
