# CLAUDE.md - Python Project AI Agent Operations Manual

## Agent Identity & Capabilities

You are an autonomous development agent for a Python package that will be published to PyPI. Your role is to maintain, test, document, and release high-quality Python code with comprehensive documentation and security compliance.

### Core Competencies
- **Language**: Python 3.9+ with type hints
- **Package Management**: uv (ultra-fast), pip, setuptools
- **Quality Tools**: ruff, black, mypy, bandit
- **Documentation**: Sphinx, ReadTheDocs, docstrings
- **Testing**: pytest, coverage, tox, hypothesis
- **Publishing**: PyPI, TestPyPI, semantic versioning

### Available MCP Servers
- **filesystem**: Read/write project files, execute commands
- **memory**: Store patterns, issues, solutions for learning
- **postgres**: Store metrics, test results, deployment history (if applicable)
- **puppeteer**: Automated documentation preview and testing (if web components)

## Critical Memory Management

### Required Memory Context
Initialize and maintain this context throughout work:

```python
memory_context = {
    "project_state": {
        "current_version": None,
        "last_deployment": None,
        "pending_changes": [],
        "test_coverage": 0.0,
        "type_coverage": 0.0,
        "security_issues": [],
        "documentation_gaps": []
    },
    "patterns": {
        "error_solutions": {},      # Error pattern -> solution mapping
        "performance_optimizations": {},
        "api_designs": {},          # Successful API patterns
        "test_strategies": {}       # Testing patterns that caught bugs
    },
    "quality_metrics": {
        "ruff_violations": [],
        "mypy_errors": [],
        "bandit_issues": [],
        "coverage_trends": [],
        "complexity_scores": {}
    },
    "release_history": {
        "versions": [],
        "changelog_entries": [],
        "breaking_changes": [],
        "deprecations": []
    },
    "documentation": {
        "api_changes": [],
        "examples_needed": [],
        "sphinx_build_issues": [],
        "readthedocs_config": {}
    }
}
```

### Memory Update Triggers

#### After Every Code Change
```python
def update_memory_after_change(file_path, change_type):
    """Store context after every modification"""
    memory["project_state"]["pending_changes"].append({
        "file": file_path,
        "type": change_type,  # feature/fix/refactor/docs
        "timestamp": datetime.now(),
        "tests_added": [],
        "docs_updated": False
    })
```

#### After Debugging Session
```python
def store_debugging_knowledge(error, solution):
    """Capture debugging patterns for future reference"""
    memory["patterns"]["error_solutions"][str(error)] = {
        "symptoms": error.__class__.__name__,
        "root_cause": analyze_root_cause(error),
        "solution": solution,
        "prevention": generate_prevention_strategy(error),
        "test_case": create_regression_test(error),
        "occurred_in": get_module_context(),
        "timestamp": datetime.now()
    }
```

#### After Quality Checks
```python
def store_quality_metrics():
    """Track quality trends over time"""
    metrics = {
        "ruff": run_ruff_check(),
        "mypy": run_mypy_check(),
        "bandit": run_security_scan(),
        "coverage": get_test_coverage(),
        "complexity": calculate_complexity()
    }
    
    memory["quality_metrics"]["history"].append({
        "timestamp": datetime.now(),
        "metrics": metrics,
        "trending": calculate_trend(metrics)
    })
```

### Memory Query Patterns

Before starting ANY task:

```python
# For feature development
memory_queries = [
    "Search for similar API patterns in this project",
    "What test strategies worked for similar features?",
    "Find all related error patterns and solutions",
    "What documentation patterns work best here?"
]

# For debugging
debug_queries = [
    "Find previous occurrences of this error type",
    "What solutions worked for similar issues?",
    "Search for related module problems",
    "What tests could have caught this?"
]

# For optimization
optimization_queries = [
    "What performance patterns improved similar code?",
    "Find all profiling results for this module",
    "What caching strategies worked before?",
    "Search for successful async conversions"
]
```

## MANDATORY Development Workflow

### The Iron Law: CODE → QUALITY → TEST → DOCUMENT → VERIFY

**EVERY change must follow this sequence without exception:**

```python
async def mandatory_development_cycle(change_description):
    """Non-negotiable workflow for ALL changes"""
    
    # 1. Make the change
    changed_files = implement_change(change_description)
    memory["pending_changes"].append(changed_files)
    
    # 2. Format with black (MANDATORY)
    subprocess.run(["uv", "run", "black", "."], check=True)
    
    # 3. Lint with ruff (MANDATORY)
    ruff_result = subprocess.run(["uv", "run", "ruff", "check", "--fix", "."], 
                                capture_output=True)
    if ruff_result.returncode != 0:
        fix_ruff_violations(ruff_result.stdout)
        return await mandatory_development_cycle(change_description)  # Retry
    
    # 4. Type check with mypy (MANDATORY)
    mypy_result = subprocess.run(["uv", "run", "mypy", "."], 
                                 capture_output=True)
    if mypy_result.returncode != 0:
        fix_type_errors(mypy_result.stdout)
        return await mandatory_development_cycle(change_description)  # Retry
    
    # 5. Security scan with bandit (MANDATORY)
    bandit_result = subprocess.run(["uv", "run", "bandit", "-r", "."], 
                                   capture_output=True)
    if "No issues identified" not in bandit_result.stdout.decode():
        fix_security_issues(bandit_result.stdout)
        return await mandatory_development_cycle(change_description)  # Retry
    
    # 6. Run tests with coverage (MANDATORY)
    test_result = subprocess.run(["uv", "run", "pytest", "--cov=.", "--cov-report=term-missing"],
                                capture_output=True)
    if test_result.returncode != 0:
        fix_failing_tests(test_result.stdout)
        return await mandatory_development_cycle(change_description)  # Retry
    
    # 7. Check coverage threshold (MANDATORY)
    coverage = extract_coverage_percentage(test_result.stdout)
    if coverage < 80.0:  # Minimum 80% coverage
        add_missing_tests(test_result.stdout)
        return await mandatory_development_cycle(change_description)  # Retry
    
    # 8. Update documentation (MANDATORY)
    update_docstrings(changed_files)
    update_sphinx_docs(changed_files)
    
    # 9. Build documentation (MANDATORY)
    sphinx_result = subprocess.run(["uv", "run", "sphinx-build", "-b", "html", "docs", "docs/_build"],
                                  capture_output=True)
    if sphinx_result.returncode != 0:
        fix_documentation_errors(sphinx_result.stderr)
        return await mandatory_development_cycle(change_description)  # Retry
    
    # 10. Verify everything passes
    final_check = run_complete_validation()
    
    # 11. Update memory with success
    memory["project_state"]["test_coverage"] = coverage
    memory["project_state"]["last_successful_change"] = datetime.now()
    
    return final_check["all_passed"]
```

## Quality Enforcement Commands

### The Holy Trinity of Python Quality

```bash
# 1. Format First (black)
uv run black .
# Why: Consistent formatting eliminates style debates

# 2. Lint Second (ruff) 
uv run ruff check --fix .
# Why: Catches bugs, enforces best practices

# 3. Type Check Third (mypy)
uv run mypy . --strict
# Why: Prevents runtime type errors
```

### Security & Safety Checks

```bash
# Security scan with bandit
uv run bandit -r . -ll  # Only medium and high severity

# Dependency vulnerability scan
uv pip audit

# License compliance check
uv run pip-licenses --with-system --allow-only="MIT;Apache-2.0;BSD-3-Clause;BSD-2-Clause"
```

### Testing Commands

```bash
# Run tests with coverage
uv run pytest --cov=. --cov-report=term-missing --cov-report=html

# Run with different Python versions
uv run tox

# Property-based testing
uv run pytest --hypothesis-profile=dev

# Mutation testing (if configured)
uv run mutmut run
```

## Documentation Workflow

### Sphinx Documentation Structure

```
docs/
├── conf.py           # Sphinx configuration
├── index.rst         # Main documentation page
├── api/             # Auto-generated API docs
│   └── modules.rst
├── guides/          # User guides
│   ├── quickstart.rst
│   └── advanced.rst
├── examples/        # Code examples
└── _static/         # Static assets
```

### Documentation Update Protocol

```python
def update_documentation_after_change(module_path):
    """Ensure docs stay synchronized with code"""
    
    # 1. Update module docstrings
    update_module_docstrings(module_path)
    
    # 2. Regenerate API documentation
    subprocess.run([
        "uv", "run", "sphinx-apidoc", 
        "-o", "docs/api", 
        "src",  # or your package directory
        "--force"
    ])
    
    # 3. Update examples if API changed
    if api_signature_changed(module_path):
        update_code_examples(module_path)
    
    # 4. Build and verify
    result = subprocess.run([
        "uv", "run", "sphinx-build", 
        "-b", "html", 
        "-W",  # Treat warnings as errors
        "docs", 
        "docs/_build"
    ], capture_output=True)
    
    if result.returncode != 0:
        fix_documentation_issues(result.stderr)
    
    # 5. Check for broken links
    subprocess.run([
        "uv", "run", "sphinx-build",
        "-b", "linkcheck",
        "docs",
        "docs/_build"
    ])
    
    # 6. Preview locally
    print("Documentation built. Preview at: docs/_build/index.html")
```

### Docstring Standards

```python
def example_function(param1: str, param2: int = 0) -> dict:
    """
    Brief description of function purpose.
    
    Longer description explaining details, edge cases,
    and any important behavior.
    
    Args:
        param1: Description of first parameter.
        param2: Description of second parameter. Defaults to 0.
    
    Returns:
        Description of return value.
    
    Raises:
        ValueError: When param1 is empty.
        TypeError: When param2 is not numeric.
    
    Examples:
        >>> example_function("test", 42)
        {'result': 'test-42'}
        
    Note:
        Any additional notes about usage or behavior.
        
    .. versionadded:: 1.2.0
    .. versionchanged:: 1.3.0
       Added support for negative param2 values.
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    
    return {'result': f'{param1}-{param2}'}
```

## Package Management with uv

### Project Setup

```bash
# Initialize new project
uv init my-package
cd my-package

# Add dependencies
uv add requests pandas numpy
uv add --dev pytest pytest-cov black ruff mypy sphinx bandit

# Create virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Sync dependencies
uv sync
```

### pyproject.toml Configuration

```toml
[project]
name = "your-package"
version = "1.0.0"
description = "Package description"
authors = [{name = "Your Name", email = "you@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.9"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Typing :: Typed",
]
dependencies = [
    "requests>=2.28.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "sphinx>=6.0.0",
    "bandit>=1.7.0",
]

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311', 'py312']

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C", "N", "D", "I", "S", "B", "A", "C4", "PT", "Q", "RET", "SIM", "ARG", "ERA", "PL"]
ignore = ["D203", "D213"]
target-version = "py39"

[tool.mypy]
python_version = "3.9"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_unimported = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
check_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-ra -q --strict-markers --cov=src --cov-report=term-missing"

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
fail_under = 80
```

## Testing Best Practices

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st

class TestFeature:
    """Group related tests in classes"""
    
    @pytest.fixture
    def setup_data(self):
        """Fixture for test data"""
        return {"key": "value"}
    
    def test_normal_behavior(self, setup_data):
        """Test the happy path"""
        result = function_under_test(setup_data)
        assert result.success is True
    
    def test_edge_case(self):
        """Test boundary conditions"""
        with pytest.raises(ValueError):
            function_under_test(None)
    
    @given(st.text())
    def test_property_based(self, input_text):
        """Property-based testing with hypothesis"""
        result = function_under_test(input_text)
        assert isinstance(result, str)
    
    @patch('module.external_service')
    def test_with_mock(self, mock_service):
        """Test with external dependencies mocked"""
        mock_service.return_value = {"mocked": True}
        result = function_under_test()
        mock_service.assert_called_once()
```

### Test Coverage Analysis

```bash
# Generate coverage report
uv run pytest --cov=. --cov-report=html --cov-report=term-missing

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Find untested code
uv run coverage report --show-missing
```

## Release & Publishing Workflow

### Semantic Versioning

```python
def determine_version_bump(changes):
    """Determine version bump based on changes"""
    
    # Check for breaking changes
    if any(c["type"] == "breaking" for c in changes):
        return "major"  # 1.0.0 -> 2.0.0
    
    # Check for new features
    if any(c["type"] == "feature" for c in changes):
        return "minor"  # 1.0.0 -> 1.1.0
    
    # Otherwise, patch version
    return "patch"  # 1.0.0 -> 1.0.1
```

### Pre-Release Checklist

```python
async def pre_release_validation():
    """Complete validation before release"""
    
    checks = {
        "tests_pass": run_all_tests(),
        "coverage_adequate": check_coverage() >= 80,
        "types_correct": run_mypy_strict(),
        "security_clean": run_bandit_scan(),
        "docs_build": build_sphinx_docs(),
        "changelog_updated": verify_changelog(),
        "version_bumped": check_version_bump(),
        "dependencies_locked": verify_dependencies()
    }
    
    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise ReleaseBlocker(f"Failed checks: {failed}")
    
    return True
```

### Publishing to PyPI

```bash
# 1. Build the package
uv build

# 2. Check the build
uv run twine check dist/*

# 3. Upload to TestPyPI first
uv run twine upload --repository testpypi dist/*

# 4. Test installation from TestPyPI
uv pip install --index-url https://test.pypi.org/simple/ your-package

# 5. Upload to PyPI
uv run twine upload dist/*

# 6. Verify installation
uv pip install your-package
```

## Error Recovery Procedures

### Common Issues & Auto-Fixes

```python
ERROR_PATTERNS = {
    "ImportError": {
        "detection": "No module named",
        "auto_fix": lambda e: install_missing_module(e),
        "prevention": "Add to requirements.txt"
    },
    "TypeError": {
        "detection": "got an unexpected keyword argument",
        "auto_fix": lambda e: update_function_signature(e),
        "prevention": "Use type hints consistently"
    },
    "AttributeError": {
        "detection": "has no attribute",
        "auto_fix": lambda e: check_api_changes(e),
        "prevention": "Version pin dependencies"
    }
}

def auto_fix_error(error):
    """Attempt automatic error resolution"""
    error_type = type(error).__name__
    
    if error_type in ERROR_PATTERNS:
        pattern = ERROR_PATTERNS[error_type]
        if pattern["detection"] in str(error):
            success = pattern["auto_fix"](error)
            if success:
                memory["patterns"]["error_solutions"][str(error)] = {
                    "auto_fixed": True,
                    "solution": pattern["prevention"]
                }
            return success
    
    return False
```

## Performance Optimization

### Profiling Protocol

```python
import cProfile
import pstats
from memory_profiler import profile

@profile
def memory_intensive_function():
    """Monitor memory usage"""
    large_list = [i for i in range(1000000)]
    return sum(large_list)

def profile_performance():
    """CPU profiling"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Code to profile
    result = function_to_profile()
    
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 time consumers
    
    # Store in memory for analysis
    memory["patterns"]["performance_optimizations"][function_to_profile.__name__] = {
        "profile_data": stats,
        "timestamp": datetime.now()
    }
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        
    - name: Install dependencies
      run: |
        uv sync
        
    - name: Format check
      run: uv run black --check .
    
    - name: Lint
      run: uv run ruff check .
    
    - name: Type check
      run: uv run mypy . --strict
    
    - name: Security scan
      run: uv run bandit -r . -ll
    
    - name: Run tests
      run: uv run pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
    
    - name: Build documentation
      run: |
        uv run sphinx-build -b html -W docs docs/_build
```

## Task Classification & Autonomy

### Level 1: Full Autonomy
- Formatting with black
- Simple linting fixes
- Docstring updates
- Test additions for existing code
- Dependency updates (patch versions)
- Documentation typo fixes

### Level 2: Guided Autonomy
- API design changes
- New feature implementation
- Refactoring modules
- Performance optimizations
- Breaking change migrations
- Complex test scenarios

### Level 3: Requires Confirmation
- Security-related changes
- Database schema modifications
- Authentication/authorization
- Major version bumps
- License changes
- Production configuration

## Success Metrics

Track these KPIs in memory:

```python
SUCCESS_METRICS = {
    "code_coverage": {"target": 80, "current": 0},
    "type_coverage": {"target": 95, "current": 0},
    "documentation_coverage": {"target": 100, "current": 0},
    "security_issues": {"target": 0, "current": 0},
    "complexity_score": {"target": "<10", "current": 0},
    "release_frequency": {"target": "weekly", "current": None},
    "bug_discovery_rate": {"target": "<1_per_release", "current": 0},
    "time_to_fix": {"target": "<1_hour", "current": 0}
}

def update_success_metrics():
    """Update and track success metrics"""
    metrics = SUCCESS_METRICS.copy()
    
    # Update current values
    metrics["code_coverage"]["current"] = get_test_coverage()
    metrics["type_coverage"]["current"] = get_type_coverage()
    metrics["documentation_coverage"]["current"] = get_doc_coverage()
    metrics["security_issues"]["current"] = count_security_issues()
    
    # Store in memory
    memory["performance_metrics"]["success_metrics"].append({
        "timestamp": datetime.now(),
        "metrics": metrics,
        "meeting_targets": all(
            m["current"] >= m["target"] 
            for m in metrics.values() 
            if isinstance(m["target"], (int, float))
        )
    })
```

## Emergency Recovery

```bash
#!/bin/bash
# Full environment recovery

# 1. Clean everything
rm -rf .venv dist build *.egg-info
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 2. Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Recreate environment
uv venv
source .venv/bin/activate

# 4. Reinstall all dependencies
uv sync

# 5. Verify everything works
uv run black --check .
uv run ruff check .
uv run mypy . --strict
uv run pytest
uv run sphinx-build -b html docs docs/_build

echo "Environment recovered successfully!"
```

## Session Workflow Templates

### New Feature Session
```python
# 1. Memory check
search_memory("similar features implemented")
search_memory("API patterns that worked")

# 2. Create feature branch
git checkout -b feature/new-feature

# 3. Implement with TDD
write_tests_first()
implement_feature()
run_mandatory_development_cycle()

# 4. Document everything
update_docstrings()
add_usage_examples()
build_documentation()

# 5. Store learnings
store_in_memory("Feature pattern: [what worked]")
```

### Debugging Session
```python
# 1. Reproduce issue
create_minimal_reproduction()
capture_error_details()

# 2. Search memory
search_memory(f"error: {error_type}")
search_memory("similar symptoms")

# 3. Fix and verify
apply_fix()
add_regression_test()
run_mandatory_development_cycle()

# 4. Document solution
store_in_memory(f"Fixed {error}: {solution}")
```

## Critical Reminders

1. **NEVER skip quality checks** - They prevent production issues
2. **ALWAYS update memory** - Learn from every session
3. **TEST everything** - Untested code is broken code
4. **DOCUMENT as you go** - Not after
5. **Security is NOT optional** - Run bandit on everything
6. **Type hints everywhere** - Future you will thank you
7. **80% coverage minimum** - No exceptions
8. **Format before commit** - Black is non-negotiable

