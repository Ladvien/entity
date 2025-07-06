# SPIKE-DX-001: Developer Experience and Hot Reload

## Summary
This spike captures recommended approaches for plugin discovery and runtime hot reload. It also lists day-to-day workflow tips for developers working on the framework.

## Discovery Approach
- Keep a `pyproject.toml` in each plugin package under `[tool.entity.plugins]`.
- The initializer scans directories listed in `plugin_dirs` to merge discovered plugins into the configuration.
- Rely on simple class paths in the metadata so packages remain importable without extra hooks.

## Hot Reload Strategy
- Plugins implement a `reconfigure(new_cfg)` method that validates and applies settings at runtime.
- The CLI exposes `reload-config updated.yaml` to watch for changes and reload after pipelines finish their current run.
- For iterative development, enable `watchfiles` to trigger reloads when code or configuration changes.

## Developer Workflow Tips
1. Install dependencies with `poetry install`.
2. Run formatters and linters before committing:
   ```bash
   poetry run black src tests
   poetry run isort src tests
   poetry run flake8 src tests
   ```
3. Validate configurations and run tests:
   ```bash
   poetry run mypy src
   bandit -r src
   python -m src.config.validator --config config/dev.yaml
   python -m src.config.validator --config config/prod.yaml
   python -m src.registry.validator
   pytest
   ```
4. Pull latest changes from `main` and resolve conflicts before pushing.
5. Use `poetry run` for all commands to ensure the virtual environment is active.
