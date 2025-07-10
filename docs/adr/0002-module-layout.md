# ADR 0002: Module Layout Simplification

## Status
Accepted

## Context
The project originally scattered core engine modules across `src/pipeline` and
`src/pipeline/user_plugins`. Plugin implementations lived in the `plugins` package.
This split caused confusion about where base classes were defined and how
framework code should be imported.

## Decision
All engine functionality now resides under `src/pipeline` while built-in plugins
live in `src/plugins`. The temporary `user_plugins` package used for backward
compatibility has been removed. Imports now reference `plugins` directly, which
clarifies intent and keeps plugin code clearly separated from the core engine.

## Consequences
- Imports are simpler (`from plugins import PromptPlugin`)
- Future modules should extend either `pipeline` or `plugins`
- Documentation references were updated to reflect the new paths

