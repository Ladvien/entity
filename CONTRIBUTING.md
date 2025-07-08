# Contributing

Thank you for helping improve Entity Pipeline Framework! Always start with `poetry install --with dev` to create the virtual environment and install dependencies. After that, follow the project guidelines and run all checks before opening a pull request.

## Code Review Expectations

- Keep pull requests focused and small.
- Describe the purpose of the change and any new dependencies.
- Ensure tests and documentation are updated when relevant.
- Maintain readable, well-structured code. Favor object oriented design.
- Pre-commit hooks run automatically. They will fail if the repository contains
  empty directories; remove them before committing.

## Development workflow

Run these commands before creating a pull request:

```bash
poetry install --with dev
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

## Quality Checks

Before running the commands below, execute `poetry install --with dev` so that
all development dependencies are available. Then, before pushing changes, run:

```bash
poetry run black src tests
poetry run isort src tests
poetry run flake8 src tests
poetry run mypy src
bandit -r src
python tools/check_empty_dirs.py
poetry run python -m src.entity_config.validator --config config/dev.yaml
poetry run python -m src.entity_config.validator --config config/prod.yaml
python -m src.registry.validator
pytest tests/integration/ -v
pytest tests/infrastructure/ -v
pytest tests/performance/ -m benchmark
```

Pre-commit also runs `tools/check_empty_dirs.py`. This tool searches for
directories that do not contain any files (even if subdirectories are present)
and rejects the commit when such directories are found. You can run it
manually with:

```bash
python tools/check_empty_dirs.py
```

## Optional Dependencies for Examples

The examples under `examples/` rely on packages such as `websockets` and `grpcio-tools`.
Install them all at once with:

```bash
poetry install --with examples
```

CI will also check docstrings with `pydocstyle`. Core modules may import plugins, but plugins must not import core modules directly.
