# Contributing

<<<<<< yvh9jp-codex/configure-pre-commit-and-enforce-quality-checks
Thank you for helping improve Entity Pipeline Framework!

## Code Review Expectations

- Keep pull requests focused and small.
- Describe the purpose of the change and any new dependencies.
- Ensure tests and documentation are updated when relevant.
- Maintain readable, well‑structured code. Favor object oriented design.

## Quality Checks

Before pushing changes, run:

```bash
poetry run black src tests
poetry run isort src tests
poetry run flake8 src tests
poetry run mypy src
```

CI will also check docstrings with `pydocstyle`.
======
Thank you for considering a contribution to Entity. Please follow the project guidelines and run all checks before opening a pull request.

* Format code with `black`.
* Sort imports using `isort`.
* Lint with `flake8` and type check with `mypy`.
* Run `bandit` for security scanning.
* Validate configurations with `python -m src.config.validator --config config/dev.yaml` and `config/prod.yaml`.
* Ensure plugin dependency validation passes via `python -m src.registry.validator`.
* Execute integration and infrastructure tests with `pytest`.
* Core modules may import plugins, but plugins **must not** import core modules directly.

>>>>>> main
