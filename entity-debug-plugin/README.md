# Entity Debug Plugin

This package provides a simple debug prompt for the Entity agent.

## Installation

Install in editable mode with development dependencies:

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
