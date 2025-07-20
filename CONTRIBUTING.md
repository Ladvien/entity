# Contributing

Thank you for helping improve the Entity Pipeline Framework!

## Development Environment Setup

Start by setting up your development environment:

```bash
poetry install --with dev
```

This installs all required development dependencies including code quality tools.

## Project Structure Guidelines

### Code Organization
- **`src/entity/core/`** - Core execution engine and orchestration logic
- **`src/entity/plugins/`** - Built-in framework plugins (use for plugins that ship with the framework)
- **`src/entity/resources/`** - Resource interfaces (memory, storage, LLM)
- **`src/entity/config/`** - Configuration models and validation
- **`src/entity/cli/`** - Developer CLI tools and utilities
- **`src/entity/utils/`** - Shared utilities (logging, retries, etc.)
- **`plugin_library/`** - Example plugins and local development plugins (not shipped with framework). See [plugin_library/README.md](plugin_library/README.md) for details.
  Use this folder as a starting point for your own plugins. Copy any sample plugin
  and modify it to fit your needs.

### Test Organization
Mirror the source structure in tests:
- **`tests/test_core/`** - Tests for core pipeline, agent, and context
- **`tests/test_plugins/`** - Tests for plugin behaviors and base classes  
- **`tests/test_resources/`** - Tests for memory, storage, and LLM resources
- **`tests/test_config/`** - Tests for configuration parsing and validation
- **`tests/test_cli/`** - Tests for CLI commands and developer tools

**Test naming:** Use `test_module_name.py` format to match the module being tested.

## Development Workflow

Before opening a pull request, run the following quality checks:

```bash
poetry run black src tests
poetry run ruff check --fix src tests
poetry run mypy src
poetry run bandit -r src
poetry run vulture src tests
poetry run unimport --remove-all src tests
```

### Configuration Validation

Always validate both development and production configurations:

```bash
poetry run entity-cli --config config/dev.yaml verify
poetry run entity-cli --config config/prod.yaml verify
poetry run python -m src.entity.core.registry_validator
```

### Running Tests

Before running any tests, install the development dependencies. Integration
tests spin up containers using Docker, so Docker **must** be installed.
The `pytest-docker` plugin is provided through the dev group and manages these
containers. Run:

```bash
poetry install --with dev  # includes pytest-asyncio
pytest
pytest tests/integration/ -v
pytest tests/infrastructure/ -v
pytest tests/performance/ -m benchmark
```

`pytest-docker` ships with the dev dependencies and exposes the `docker_ip` and `docker_services` fixtures used in integration tests.

`pytest-asyncio` must be installed; without it pytest reports
`Unknown config option: asyncio_mode`.

**Test requirements:**
- Add tests for all new functionality
- Follow the test structure mirroring `src/entity/`
- Test both success and failure scenarios
- Include integration tests for plugin interactions

## Plugin Development Guidelines

### Plugin Location Rules
- **Built-in plugins:** Add to `src/entity/plugins/` if the plugin ships with the framework
- **Example/demo plugins:** Add to `plugin_library/` for examples, local development, or sharing. See [plugin_library/README.md](plugin_library/README.md) for details.
- **Custom plugins:** Users develop in `plugin_library/` or their own repositories

### Plugin Architecture Rules
- **Import restrictions:** Plugins must NOT import core modules directly (enforces architectural boundaries)
- **Allowed imports:** Plugin base classes, resource interfaces, and utility functions are permitted
- **Stage assignment:** Always explicitly declare plugin stages in configuration or class definition
- **Stage mismatch warnings:** When configuration overrides class stages the initializer logs a message like `MyPlugin configured stages [REVIEW] override class stages [DO]`.
- **Dependencies:** Use explicit dependency declarations rather than constructor injection

### Plugin Testing
- Add tests to `tests/test_plugins/`
- Test plugin initialization, execution, and error handling
- Verify stage assignments and dependencies
- Include configuration validation tests

## Documentation Requirements

### Code Documentation
- **Docstrings:** Use proper docstring formatting (enforced by `pydocstyle` in CI)
- **Type hints:** Add comprehensive type annotations for `mypy` validation
- **Architecture updates:** Update `ARCHITECTURE.md` when making structural changes

### Configuration Documentation
- **New config options:** Add examples to both `config/dev.yaml` and `config/prod.yaml`
- **Breaking changes:** Update configuration migration guides
- **Validation rules:** Document new validation requirements

## Pull Request Guidelines

### Code Quality Requirements
- **No backward compatibility:** This is a pre-alpha project. Remove unused code rather than maintaining backward compatibility.
- **Delete-first mindset:** When adding new features, actively look for old code to remove.
- **Code removal identification:** During PR reviews, identify any code that can be deleted.
- **Architecture compliance:** Follow all guidelines in `ARCHITECTURE.md`

### PR Process
- Keep pull requests small and focused.
- Provide a clear description of the change.
- List any new dependencies or configuration updates.
- Ensure relevant tests and documentation are updated.
- Maintain clean, readable, object-oriented code.
- Verify plugin stage assignments and error handling.
- Add `TODO:` comments when scope is unclear but work needs to continue.

### Review Guidelines
- **Reviewers must:** Identify opportunities for code deletion
- **Verify:** All architectural boundaries are maintained
- **Check:** Configuration changes work in both dev and prod
- **Validate:** New plugins follow stage assignment rules

## Configuration Guidelines

### When to Update Configs
- **Add new features:** Update both `config/dev.yaml` and `config/prod.yaml` with examples
- **Change validation rules:** Ensure existing configs remain valid
- **Add new resources:** Include reasonable defaults and documentation

### Config Testing
- Always test configuration changes against both dev and prod configs
- Verify that configuration validation catches expected errors
- Test hot-reload scenarios for parameter-only changes

## Architecture Guidelines

**You must adhere to architectural guidelines when making changes.** See `ARCHITECTURE.md` for the complete 31-point architectural decision summary.

### Critical Architectural Boundaries

**4-Layer Resource Architecture (Decision #1):**
- Layer 1: Infrastructure Plugins (no dependencies)
- Layer 2: Resource Interface Plugins (depend only on Layer 1)
- Layer 3: Canonical Agent Resources (depend only on Layer 2) 
- Layer 4: Custom Agent Resources (depend only on Layer 3)
- Plugins can depend on any agent resources (Layer 3+)

**Plugin System Rules:**
- **Import restrictions**: Plugins must NOT import core modules directly (enforces architectural boundaries)
- **Dependency injection**: Resources use post-construction dependency injection via container
- **Stage assignment**: Follow explicit config > class defaults > THINK fallback precedence (Decision #4)
- **Response control**: Only OUTPUT stage plugins may set final responses via `context.say()` (Decision #7)
- **Fail-fast execution**: Any plugin failure immediately terminates stage and triggers ERROR stage (Decision #15)

**Pipeline Flow:**
```
INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
```
- Pipeline loops until OUTPUT plugin calls `context.say()` or max iterations reached
- Use `context.think()` and `context.reflect()` for inter-stage communication (Decision #8)

**State Management (Decision #23):**
- **Anthropomorphic methods**: `remember()`, `recall()`, `think()`, `reflect()`, `say()` for simple cases
- **Advanced Memory resource**: Direct SQL queries, vector search for complex operations
- **External persistence**: All data stored in database/external storage, never in worker memory
- **User isolation**: Automatic namespacing via `user_id` parameter (Decision #29)

**Progressive Disclosure (Decision #2):**
- Layer 0: Zero-config with `@agent.tool`, `@agent.prompt` decorators
- Layer 1: Function decorators with auto-classification  
- Layer 2: Class-based plugins with explicit control
- Layer 3: Advanced plugins with sophisticated pipeline access

## Optional Dependencies for Examples

Examples in `examples/` may require additional packages like `websockets` and `grpcio-tools`. To install:

```bash
poetry install --with examples
```

## Notes

- CI will run all checks automatically, including documentation formatting.
- Keep documentation updated to reflect current reality - refer to `ARCHITECTURE.md` for the living architecture documentation with 31 architectural decisions.
- Use the principle checklist in `docs/source/principle_checklist.md` to verify architectural compliance.
- **Layer 0 Development**: Framework supports zero-config development with `@agent.tool`, `@agent.prompt` decorators for rapid prototyping.
- **Stateless Workers**: All user state persists externally; workers load/save state per request (Decision #6).
- **Auto-injection**: `metrics_collector` resource automatically injected into all plugins for unified performance tracking (Decision #31).