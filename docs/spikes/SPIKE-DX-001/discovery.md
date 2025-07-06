# SPIKE-DX-001: Plugin Discovery Exploration

## Summary
This spike explores ways to automatically discover and reload plugins.
The goals are to simplify dynamic loading and to support iterative plugin
development without restarting the whole pipeline.

## Entry Points
- Python packages can expose plugin classes via the `entry_points` table in
  `pyproject.toml`.
- Each entry point maps a group name to an import path. Loading tools can iterate
  over `importlib.metadata.entry_points(group="entity.plugins")` to gather
  registered plugins.

## Directory Scanning
- When entry points are not available, scanning plugin directories also works.
- `Path.iterdir()` can list candidate modules within a folder such as
  `user_plugins`.
- Combining `importlib.import_module` with a naming convention (e.g., files
  ending in `_plugin.py`) helps locate plugin classes at runtime.

## Reloading Modules
- `importlib.reload(module)` refreshes an already imported plugin module.
- This allows live changes during development without restarting the process.
- Care must be taken to update references, as reloading only replaces the
  module object.

## Plugin Metadata
- The project's `pyproject.toml` demonstrates metadata fields under
  `[tool.poetry]` such as name, version and dependencies.
- Plugin packages can extend this file with an `[project.entry-points]` section
  to advertise available plugins.

