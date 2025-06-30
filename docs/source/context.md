# Plugin Context

The `PluginContext` object gives each plugin a safe interface to
interact with the running pipeline. It exposes helper methods for
calling tools, retrieving resources, recording stage results and
updating conversation history. Plugins never manipulate the internal
`PipelineState` directly; instead they use `PluginContext` for all
stateful operations.

See the API reference for `pipeline.context.PluginContext` for a
complete list of methods.
