# Entity Development Guide

## Code Quality Standards

### Required for All Code

1. **Formatting**: All code must pass `black` formatting
2. **Imports**: Must be organized with `isort`
3. **Linting**: Must pass `ruff` checks
4. **Type Hints**: All functions must have type hints (enforced by `mypy`)
5. **Security**: Must pass `bandit` security scan
6. **Test Coverage**: Minimum 80% coverage required

### Pre-commit Hooks

Pre-commit hooks are configured and must pass before commits:

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Development Workflow

### 1. Setting Up Development Environment

```bash
# Clone with submodules
git clone --recursive https://github.com/Ladvien/entity.git
cd entity

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 2. Making Changes

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes
# ...

# Run quality checks
poetry run black src/ tests/
poetry run isort src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/
poetry run bandit -r src/

# Run tests
poetry run pytest tests/ --cov=src/entity
```

### 3. Commit Standards

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

### 4. Creating Checkpoints

For significant milestones:

```bash
# Create checkpoint branch
git checkout -b checkpoint-XX

# Commit and push
git add -A
git commit -m "checkpoint-XX: Description"
git push origin checkpoint-XX

# Merge to main (no-delete)
git checkout main
git merge checkpoint-XX
git push origin main
```

## Architecture Guidelines

### Plugin Development

1. All plugins must inherit from `Plugin` base class
2. Implement required methods: `execute`, `validate`
3. Use type hints for all parameters and return values
4. Include comprehensive docstrings

Example:

```python
from entity.plugins.base import Plugin
from entity.plugins.context import PluginContext

class MyPlugin(Plugin):
    """Brief description of plugin."""

    supported_stages = ["INPUT", "OUTPUT"]

    async def execute(self, context: PluginContext) -> PluginContext:
        """Execute plugin logic."""
        # Implementation
        return context

    async def validate(self, context: PluginContext) -> bool:
        """Validate plugin can execute."""
        return True
```

### Resource Management

1. Use context managers for resources
2. Implement proper cleanup in `__aexit__`
3. Handle exceptions gracefully
4. Log all errors appropriately

### Testing Standards

1. Write tests for all new features
2. Use pytest fixtures for setup
3. Mock external dependencies
4. Test both success and failure cases

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def setup_data():
    """Fixture for test data."""
    return {"key": "value"}

async def test_feature(setup_data):
    """Test feature description."""
    result = await function_under_test(setup_data)
    assert result.success is True
```

## Performance Guidelines

### Optimization Priorities

1. **Correctness** > Performance
2. **Readability** > Cleverness
3. **Maintainability** > Micro-optimizations

### Memory Management

- Clear collections when done: `list.clear()`, `dict.clear()`
- Use generators for large datasets
- Implement `__slots__` for frequently instantiated classes
- Profile memory usage for critical paths

### Async Best Practices

- Use `async`/`await` for I/O operations
- Batch operations when possible
- Implement proper cancellation handling
- Use `asyncio.gather()` for concurrent operations

## Security Guidelines

### Never Commit

- API keys, tokens, or secrets
- Personal information
- Internal URLs or endpoints
- Debug output with sensitive data

### Always Validate

- User input sanitization
- SQL injection prevention
- Path traversal protection
- Command injection prevention

## Documentation Standards

### Docstrings (Google Style)

```python
def function(param1: str, param2: int) -> dict:
    """Brief description.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is invalid.
    """
```

### README Updates

Update README.md when:
- Adding new features
- Changing API
- Modifying installation steps
- Adding dependencies

## Monitoring & Maintenance

### Regular Tasks

**Daily:**
- Check CI/CD pipeline status
- Review error logs

**Weekly:**
- Run full test suite locally
- Check dependency updates
- Review open issues

**Monthly:**
- Performance profiling
- Security audit
- Documentation review

### Code Cleanup Checklist

Run periodically (stored in memory as "Cleanup Checklist"):

1. Remove dead code (vulture)
2. Find duplicates (pylint)
3. Fix imports (autoflake, isort)
4. Format code (black)
5. Type checking (mypy)
6. Security scan (bandit)
7. Test coverage check
8. Documentation updates

## Release Process

### Version Bumping

Follow semantic versioning:
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

### Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run full test suite
4. Create git tag: `git tag v1.2.3`
5. Push tag: `git push origin v1.2.3`
6. GitHub Actions will handle PyPI release

## Getting Help

- **Issues**: https://github.com/Ladvien/entity/issues
- **Discussions**: https://github.com/Ladvien/entity/discussions
- **Documentation**: See `/docs` directory

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Ensure all checks pass
5. Submit pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.
