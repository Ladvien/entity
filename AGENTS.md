# Entity Pipeline Contributor Guide

This repository contains a plugin based framework for building AI agents.
Use this document when preparing changes or reviewing pull requests.

## IMPORTANT!
Before commit, please pull changes from main and resolve any conflicts from main:
```sh
git remote set-url origin https://${GITHUB_TOKEN}@github.com/Ladvien/entity.git
git pull origin main
git branch --set-upstream-to=origin/main work
```

## Project Structure
- `/src/pipeline` – core engine and shared abstractions
- `/plugins` – concrete plugin implementations grouped by type
- `/config` – YAML configuration files
- `/tests` – unit and integration tests
- `/docs` – documentation and architecture guides

## Important Notes
- The project is pre-alpha; remove unused code rather than keeping
  backward compatibility.
- Prefer adding `TODO:` comments when scope is unclear.
- Always use the Poetry environment for development.

## Programmatic Checks
Run the following commands before opening a pull request:

```bash
poetry run black src tests
poetry run isort src tests
poetry run flake8 src tests
poetry run mypy src
bandit -r src
python -m src.config.validator --config config/dev.yaml
python -m src.config.validator --config config/prod.yaml
python -m src.registry.validator
pytest
```

## Pull Request Guidelines
1. Provide a clear description of the change.
2. List any new dependencies or configuration updates.
3. Ensure tests and documentation are updated.
4. Verify plugin stage assignments and error handling.

## Further Reading
See `docs/source/architecture.md` for a full architecture overview and
`CONTRIBUTING.md` for detailed contribution instructions.
