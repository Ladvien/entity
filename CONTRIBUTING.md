# Contributing

<<<<<<< HEAD
<<<<<< yvh9jp-codex/configure-pre-commit-and-enforce-quality-checks
=======
>>>>>>> 9d6a2313c36e05a741a2a9b374ba1bfd354e9bd2
Thank you for helping improve Entity Pipeline Framework!

## Code Review Expectations

- Keep pull requests focused and small.
- Describe the purpose of the change and any new dependencies.
- Ensure tests and documentation are updated when relevant.
<<<<<<< HEAD
- Maintain readable, well‑structured code. Favor object oriented design.
=======
- Maintain readable, well-structured code. Favor object oriented design.
>>>>>>> 9d6a2313c36e05a741a2a9b374ba1bfd354e9bd2

## Quality Checks

Before pushing changes, run:

```bash
poetry run black src tests
poetry run isort src tests
poetry run flake8 src tests
poetry run mypy src
<<<<<<< HEAD
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
=======
bandit -r src
python -m src.config.validator --config config/dev.yaml
python -m src.config.validator --config config/prod.yaml
python -m src.registry.validator
pytest tests/integration/ -v
pytest tests/infrastructure/ -v
pytest tests/performance/ -m benchmark
```

CI will also check docstrings with `pydocstyle`.
>>>>>>> 9d6a2313c36e05a741a2a9b374ba1bfd354e9bd2
