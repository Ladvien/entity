# Plugin Execution Order

Plugins are executed in the order they are registered. The `PluginRegistry`
stores plugins in an `OrderedDict` so iteration yields them in exactly the
same sequence in which they were added. Both `get_plugins_for_stage()` and
`list_plugins()` return plugins in registration order, guaranteeing
deterministic execution whenever multiple plugins share a stage.

