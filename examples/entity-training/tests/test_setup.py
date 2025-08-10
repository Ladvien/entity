"""Tests for entity-training plugin setup and structure."""

from pathlib import Path

import pytest


class TestProjectStructure:
    """Test that the project structure is correctly set up."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def test_directory_structure_exists(self, project_root):
        """Test that all required directories exist."""
        required_dirs = [
            "plugins",
            "configs",
            "data",
            "models",
            "tests",
            "scripts",
        ]

        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_name} does not exist"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_init_files_exist(self, project_root):
        """Test that __init__.py files exist in Python packages."""
        packages = ["plugins", "tests"]

        for package in packages:
            init_file = project_root / package / "__init__.py"
            assert init_file.exists(), f"__init__.py missing in {package}"
            assert init_file.is_file(), f"__init__.py in {package} is not a file"

    def test_gitkeep_files_exist(self, project_root):
        """Test that .gitkeep files exist in data directories."""
        gitkeep_locations = ["data/.gitkeep", "models/.gitkeep"]

        for location in gitkeep_locations:
            gitkeep_file = project_root / location
            assert gitkeep_file.exists(), f".gitkeep missing at {location}"

    def test_configuration_files_exist(self, project_root):
        """Test that configuration files are present."""
        config_files = [
            "pyproject.toml",
            ".env.example",
            ".gitignore",
            "setup.cfg",
            "README.md",
        ]

        for config_file in config_files:
            file_path = project_root / config_file
            assert file_path.exists(), f"Configuration file {config_file} does not exist"
            assert file_path.is_file(), f"{config_file} is not a file"

    def test_sample_data_exists(self, project_root):
        """Test that sample data file exists."""
        sample_data = project_root / "data" / "sample.jsonl"
        assert sample_data.exists(), "Sample data file does not exist"
        assert sample_data.is_file(), "Sample data is not a file"

        # Check that it contains valid JSONL
        import json

        with open(sample_data, "r") as f:
            lines = f.readlines()
            assert len(lines) > 0, "Sample data file is empty"

            for i, line in enumerate(lines):
                try:
                    data = json.loads(line)
                    assert "input" in data, f"Line {i+1} missing 'input' field"
                    assert "output" in data, f"Line {i+1} missing 'output' field"
                except json.JSONDecodeError as e:
                    pytest.fail(f"Line {i+1} is not valid JSON: {e}")


class TestPyprojectConfiguration:
    """Test the pyproject.toml configuration."""

    @pytest.fixture
    def pyproject_path(self):
        """Get the pyproject.toml path."""
        return Path(__file__).parent.parent / "pyproject.toml"

    def test_pyproject_valid_toml(self, pyproject_path):
        """Test that pyproject.toml is valid TOML."""
        import toml

        try:
            with open(pyproject_path, "r") as f:
                config = toml.load(f)
        except Exception as e:
            pytest.fail(f"pyproject.toml is not valid TOML: {e}")

        assert config is not None, "pyproject.toml is empty"

    def test_pyproject_has_required_sections(self, pyproject_path):
        """Test that pyproject.toml has all required sections."""
        import toml

        with open(pyproject_path, "r") as f:
            config = toml.load(f)

        # Check for Poetry configuration
        assert "tool" in config, "Missing [tool] section"
        assert "poetry" in config["tool"], "Missing [tool.poetry] section"

        poetry_config = config["tool"]["poetry"]
        required_fields = ["name", "version", "description", "authors"]

        for field in required_fields:
            assert field in poetry_config, f"Missing {field} in [tool.poetry]"

        # Check dependencies
        assert "dependencies" in poetry_config, "Missing dependencies section"
        assert "python" in poetry_config["dependencies"], "Missing Python version specification"

    def test_pyproject_dependencies(self, pyproject_path):
        """Test that required dependencies are specified."""
        import toml

        with open(pyproject_path, "r") as f:
            config = toml.load(f)

        dependencies = config["tool"]["poetry"]["dependencies"]
        required_deps = [
            "entity-core",
            "torch",
            "transformers",
            "datasets",
            "peft",
        ]

        for dep in required_deps:
            assert dep in dependencies, f"Missing required dependency: {dep}"


class TestEnvironmentConfiguration:
    """Test environment configuration files."""

    @pytest.fixture
    def env_example_path(self):
        """Get the .env.example path."""
        return Path(__file__).parent.parent / ".env.example"

    def test_env_example_exists(self, env_example_path):
        """Test that .env.example exists and contains required variables."""
        assert env_example_path.exists(), ".env.example does not exist"

        with open(env_example_path, "r") as f:
            content = f.read()

        required_vars = [
            "CUDA_VISIBLE_DEVICES",
            "HF_TOKEN",
            "DEFAULT_BATCH_SIZE",
            "DEFAULT_LEARNING_RATE",
        ]

        for var in required_vars:
            assert var in content, f"Missing environment variable: {var}"

    def test_gitignore_configuration(self):
        """Test that .gitignore is properly configured."""
        gitignore_path = Path(__file__).parent.parent / ".gitignore"
        assert gitignore_path.exists(), ".gitignore does not exist"

        with open(gitignore_path, "r") as f:
            content = f.read()

        important_patterns = [
            "__pycache__",
            ".env",
            "*.pyc",
            ".pytest_cache",
            "models/*",
            "data/*",
        ]

        for pattern in important_patterns:
            assert pattern in content, f"Missing gitignore pattern: {pattern}"


class TestReadmeDocumentation:
    """Test README documentation completeness."""

    @pytest.fixture
    def readme_path(self):
        """Get the README.md path."""
        return Path(__file__).parent.parent / "README.md"

    def test_readme_exists(self, readme_path):
        """Test that README.md exists."""
        assert readme_path.exists(), "README.md does not exist"
        assert readme_path.stat().st_size > 100, "README.md appears to be empty"

    def test_readme_has_required_sections(self, readme_path):
        """Test that README has all required sections."""
        with open(readme_path, "r") as f:
            content = f.read().lower()

        required_sections = [
            "requirements",
            "installation",
            "usage",
            "project structure",
            "testing",
        ]

        for section in required_sections:
            assert section in content, f"README missing section: {section}"

    def test_readme_has_gpu_warning(self, readme_path):
        """Test that README includes GPU memory requirements."""
        with open(readme_path, "r") as f:
            content = f.read().lower()

        assert "gpu" in content, "README should mention GPU requirements"
        assert "memory" in content, "README should mention memory requirements"


class TestPluginPackage:
    """Test the plugins package structure."""

    @pytest.fixture
    def plugins_path(self):
        """Get the plugins package path."""
        return Path(__file__).parent.parent / "plugins"

    def test_plugins_init_imports(self, plugins_path):
        """Test that plugins __init__.py has proper imports."""
        init_file = plugins_path / "__init__.py"
        assert init_file.exists(), "plugins/__init__.py does not exist"

        with open(init_file, "r") as f:
            content = f.read()

        assert "__version__" in content, "plugins/__init__.py should define __version__"

    def test_plugins_importable(self):
        """Test that the plugins package can be imported."""
        import sys

        # Add parent directory to path
        parent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(parent_dir))

        try:
            import plugins

            assert hasattr(plugins, "__version__"), "plugins module missing __version__"
        except ImportError as e:
            pytest.fail(f"Cannot import plugins package: {e}")
        finally:
            # Clean up sys.path
            sys.path.pop(0)
