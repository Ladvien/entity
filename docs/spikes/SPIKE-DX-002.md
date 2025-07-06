# SPIKE-DX-002: Developer Tooling and Testing Guidelines

## Summary
This spike consolidates recommended tooling and test practices for the Entity Pipeline Framework. It references existing contributor guides and spike documents to provide a single overview.

## Tooling Recommendations
- **Use Poetry for environment setup**. Run `poetry install --with dev` to install dependencies and create the virtual environment.
- **Pull from `main` before committing** to avoid conflicts:
  ```bash
  git remote set-url origin https://${GITHUB_TOKEN}@github.com/Ladvien/entity.git
  git pull origin main
  git branch --set-upstream-to=origin/main work
  ```
- **Run quality checks** prior to a pull request:
  ```bash
  poetry run black src tests
  poetry run isort src tests
  poetry run flake8 src tests
  poetry run mypy src
  bandit -r src
  python -m src.entity_config.validator --config config/dev.yaml
  python -m src.entity_config.validator --config config/prod.yaml
  python -m src.registry.validator
  pytest
  ```
  CI also executes `pydocstyle` to enforce docstring quality.
- **Leverage Poe tasks** from `pyproject.toml` for convenience:
  - `poe lint` runs formatting and static analysis.
  - `poe validate` checks configuration files.
  - `poe check` runs the full suite of linting, type checks, security scans, validation, and tests.

## Testing Strategies
- **Organize tests with `pytest` markers**. The configuration defines markers such as `unit`, `integration`, `slow`, and `benchmark` for selective runs.
- **Use in-memory caches for unit tests** to avoid I/O overhead and clear state between cases.
- **Benchmark performance** with the `pytest-benchmark` plugin when possible.
- **Mock individual components** thanks to the framework's modular design, keeping mental models simple.
- The CI workflow runs unit tests, integration tests, and example tests in separate jobs.

## Next Steps
Automate benchmark runs in CI and expand documentation around cache configuration. These improvements will make testing more consistent across environments.
