# Entity Debug Plugin

This package provides a simple debug prompt for the Entity agent.

## Installation

Install in editable mode with development dependencies.
Running the command below installs `entity` and all of its dependencies,
including `grpcio`:

```bash
poetry install --with dev
```

## Usage

Point `plugin_dirs` at this package when running the agent:

```yaml
plugin_dirs:
  - path/to/entity-debug-plugin
```

This ensures the `DebugPrompt` is discovered and loaded.
