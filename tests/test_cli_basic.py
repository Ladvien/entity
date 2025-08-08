"""Test CLI functionality without heavy dependencies."""

import tempfile
from pathlib import Path


def test_cli_argument_parsing():
    """Test CLI argument parsing works correctly."""
    import sys

    # Add src to path to avoid dependency issues
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    from entity.cli.__main__ import parse_args

    # Test init command parsing
    args = parse_args(["init", "test_project", "--quiet", "--no-deps"])
    assert args.command == "init"
    assert args.project_name == "test_project"
    assert args.quiet is True
    assert args.no_deps is True

    # Test run command parsing
    args = parse_args(["run", "--workflow", "test.yaml", "--verbose"])
    assert args.command == "run"
    assert args.workflow == "test.yaml"
    assert args.verbose is True


def test_init_project_structure():
    """Test that init creates correct project structure."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    from entity.cli.commands.init import create_env_example, create_project_structure

    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()

        # Create project structure
        create_project_structure(project_path, "basic")
        create_env_example(project_path, "ollama")

        # Check expected files exist
        expected_files = [
            project_path / "main.py",
            project_path / "README.md",
            project_path / ".env.example",
            project_path / "workflows" / "basic.yaml",
            project_path
            / "tests"
            / f"test_{project_path.name.lower().replace('-', '_')}.py",
        ]

        for file_path in expected_files:
            assert file_path.exists(), f"Expected file {file_path} was not created"

        # Check directories exist
        expected_dirs = [
            project_path / "src",
            project_path / "tests",
            project_path / "data",
            project_path / "workflows",
            project_path / "plugins",
        ]

        for dir_path in expected_dirs:
            assert (
                dir_path.exists() and dir_path.is_dir()
            ), f"Expected directory {dir_path} was not created"

        # Check README contains project name
        readme_content = (project_path / "README.md").read_text()
        assert "test_project" in readme_content

        # Check .env.example contains Ollama config
        env_content = (project_path / ".env.example").read_text()
        assert "OLLAMA_BASE_URL" in env_content


def test_llm_service_detection():
    """Test LLM service detection logic."""
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

    from entity.cli.commands.init import detect_llm_services

    # This should not crash and return a dict
    services = detect_llm_services()
    assert isinstance(services, dict)

    # Should have expected service keys
    expected_services = ["ollama", "openai", "anthropic", "gemini"]
    for service in expected_services:
        assert service in services
        assert "available" in services[service]
        assert "status" in services[service]
        assert "models" in services[service]


if __name__ == "__main__":
    test_cli_argument_parsing()
    test_init_project_structure()
    test_llm_service_detection()
    print("✅ All CLI tests passed!")
