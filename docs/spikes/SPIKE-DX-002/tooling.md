# SPIKE-DX-002: Developer Tooling Evaluation

## Summary
This spike assesses tools that streamline project setup and improve daily development. The focus areas are scaffolding, type checking, test isolation, and documentation generation.

## Scaffolding Options
### 1. Cookiecutter
- Widely adopted for templated project generation.
- Uses simple Jinja templates; easy for newcomers.
- Limited interactive features.

### 2. Copier
- Supports template updates after a project is created.
- More configuration flexibility than Cookiecutter.
- Slightly steeper learning curve.

**Recommendation**: Copier offers better long–term maintainability because templates can be reapplied when shared tooling evolves.

## Type Checking
- **Mypy** provides mature support and integrates with existing CI.
- **Pyright** offers faster checking and good VS Code integration.

Either tool can enforce strict typing. Mypy is already in use, so adoption requires no migration.

## Testing Isolation
- **Pytest** fixtures combined with `tmp_path` handle most isolation needs.
- For more complex environments, **Nox** can orchestrate disposable virtualenvs per session.

## Documentation Generation
- **Sphinx** is currently used for API docs and architecture guides.
- **MkDocs** has a simpler theme system but less powerful extensibility.

Sticking with Sphinx keeps consistency and leverages existing extensions.

## Next Steps
1. Prototype a Copier template for new plugins.
2. Consider running Pyright in addition to Mypy for editor feedback.
3. Evaluate Nox for integration tests that need dedicated environments.
