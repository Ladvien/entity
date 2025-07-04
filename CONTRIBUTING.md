# Contributing

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
