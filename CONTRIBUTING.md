Here’s a cleaned-up and deduplicated version of your `CONTRIBUTING.md` section. Redundant sections like repeated command blocks and overlapping workflow guidance have been consolidated under clear headings.

# Contributing

Thank you for helping improve the Entity Pipeline Framework!

Start by setting up your development environment:

```bash
poetry install --with dev
```

This installs all required development dependencies.

## Development Workflow

Before opening a pull request:

1. **Code Quality & Static Analysis**

   ```bash
   poetry run black src tests
   poetry run isort src tests
   poetry run flake8 src tests
   poetry run mypy src
   bandit -r src
   python tools/check_empty_dirs.py
   ```

2. **Configuration Validation**

   ```bash
   poetry run python -m src.entity_config.validator --config config/dev.yaml
   poetry run python -m src.entity_config.validator --config config/prod.yaml
   python -m src.registry.validator
   ```

3. **Run Tests**

   ```bash
   pytest
   pytest tests/integration/ -v
   pytest tests/infrastructure/ -v
   pytest tests/performance/ -m benchmark
   ```

Pre-commit hooks will enforce these checks automatically. The `check_empty_dirs.py` script will block commits if empty directories (without any files) are found—even if they contain subdirectories. Run it manually when needed:

```bash
python tools/check_empty_dirs.py
```

## Pull Request Guidelines

* Keep pull requests small and focused.
* Provide a clear description of the change.
* List any new dependencies or configuration updates.
* Ensure relevant tests and documentation are updated.
* Maintain clean, readable, object-oriented code.
* Verify plugin stage assignments and error handling.

## Optional Dependencies for Examples

Examples in `examples/` may require additional packages like `websockets` and `grpcio-tools`. To install:

```bash
poetry install --with examples
```

## Notes

* CI will run all checks automatically, including `pydocstyle` for docstring formatting.
* Core modules may import plugins, but **plugins must not import core modules** directly (enforces architectural boundaries).

