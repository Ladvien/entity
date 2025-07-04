# Module Map

This document describes the key modules and their responsibilities after consolidating the base plugin classes.

## `pipeline.base_plugins`
All abstract plugin base classes live in this module. Other packages import from here rather than maintaining duplicates.

## `plugins`
Concrete plugin implementations organized by type. The package re-exports the base classes for backward compatibility but no longer defines them.

## `pipeline`
The package root exposes the public API. It imports base classes from `pipeline.base_plugins` and re-exports them as convenience symbols alongside utility functions, registries and managers.
