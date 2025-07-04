# Contributing

Thank you for considering a contribution to Entity. Please follow the project guidelines and run all checks before opening a pull request.

* Format code with `black`.
* Sort imports using `isort`.
* Lint with `flake8` and type check with `mypy`.
* Run `bandit` for security scanning.
* Validate configurations with `python -m src.config.validator --config config/dev.yaml` and `config/prod.yaml`.
* Ensure plugin dependency validation passes via `python -m src.registry.validator`.
* Execute integration and infrastructure tests with `pytest`.
* Core modules may import plugins, but plugins **must not** import core modules directly.

