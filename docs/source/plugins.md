# Plugin Execution Order

Plugins are executed in the order they are registered. The `PluginRegistry`
uses an ordered dictionary so iteration yields plugins in the same sequence
in which they were added. Workflows select which plugins run at each stage,
but the registry guarantees deterministic execution when multiple plugins
share a stage.

