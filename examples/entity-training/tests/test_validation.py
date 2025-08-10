"""Validation tests to ensure the entity-training setup is complete."""

import json
from pathlib import Path

import pytest


def test_project_ready_for_development():
    """Integration test to verify the project is ready for development."""
    project_root = Path(__file__).parent.parent

    # Check critical files exist
    critical_files = [
        "pyproject.toml",
        "README.md",
        ".gitignore",
        "plugins/__init__.py",
        "tests/__init__.py",
    ]

    missing_files = []
    for file_path in critical_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    assert len(missing_files) == 0, f"Missing critical files: {missing_files}"

    # Verify sample data is valid
    sample_data_path = project_root / "data" / "sample.jsonl"
    assert sample_data_path.exists(), "Sample data file missing"

    with open(sample_data_path, "r") as f:
        lines = f.readlines()
        assert len(lines) >= 3, "Sample data should have at least 3 examples"

        for line in lines:
            data = json.loads(line.strip())
            assert "input" in data and "output" in data, "Invalid data format"

    print("✅ Project structure validated successfully!")
    print(f"📁 Project root: {project_root}")
    print(f"📊 Sample data entries: {len(lines)}")
    print("🚀 Ready for development!")


def test_dependencies_configuration():
    """Test that dependency configuration is valid."""
    project_root = Path(__file__).parent.parent

    try:
        import toml
    except ImportError:
        pytest.skip("toml package not installed")

    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        config = toml.load(f)

    deps = config["tool"]["poetry"]["dependencies"]

    # Check core dependencies
    assert "python" in deps, "Python version not specified"
    assert deps["python"].startswith("^3.11"), "Python 3.11+ required"

    # Check ML dependencies
    ml_deps = ["torch", "transformers", "datasets", "peft"]
    for dep in ml_deps:
        assert dep in deps, f"Missing ML dependency: {dep}"

    print("✅ Dependencies configuration validated!")
    print(f"📦 Total dependencies: {len(deps)}")
    print(f"🐍 Python version: {deps['python']}")


def test_entity_framework_compatibility():
    """Test that the plugin structure is compatible with Entity Framework."""
    project_root = Path(__file__).parent.parent

    # Check if we're in the Entity Framework structure
    entity_root = project_root.parent.parent
    if (entity_root / "src" / "entity").exists():
        print("✅ Located within Entity Framework structure")
        print(f"📍 Entity root: {entity_root}")
    else:
        print("⚠️  Running as standalone project (not in Entity Framework)")

    # Verify plugin package structure
    plugins_dir = project_root / "plugins"
    assert plugins_dir.exists(), "plugins directory missing"
    assert (plugins_dir / "__init__.py").exists(), "plugins/__init__.py missing"

    print("✅ Plugin structure compatible with Entity Framework!")


def test_documentation_completeness():
    """Test that documentation is complete and informative."""
    project_root = Path(__file__).parent.parent
    readme_path = project_root / "README.md"

    with open(readme_path, "r") as f:
        readme_content = f.read()

    # Check for important sections
    important_keywords = [
        "Entity Training Plugin",
        "Requirements",
        "Installation",
        "Usage",
        "GPU",
        "Fine-tuning",
        "LoRA",
    ]

    missing_keywords = []
    for keyword in important_keywords:
        if keyword.lower() not in readme_content.lower():
            missing_keywords.append(keyword)

    assert len(missing_keywords) == 0, f"README missing important topics: {missing_keywords}"

    # Check README size indicates comprehensive documentation
    assert len(readme_content) > 2000, "README seems too short for comprehensive documentation"

    print("✅ Documentation is comprehensive!")
    print(f"📝 README size: {len(readme_content)} characters")
    print("📚 All important topics covered")


if __name__ == "__main__":
    """Run validation tests directly."""
    print("\n" + "=" * 50)
    print("🔍 Entity Training Plugin Validation")
    print("=" * 50 + "\n")

    try:
        test_project_ready_for_development()
        print()
        test_dependencies_configuration()
        print()
        test_entity_framework_compatibility()
        print()
        test_documentation_completeness()
        print("\n" + "=" * 50)
        print("✅ ALL VALIDATIONS PASSED!")
        print("=" * 50 + "\n")
    except AssertionError as e:
        print(f"\n❌ Validation failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n⚠️  Unexpected error: {e}")
        exit(1)
