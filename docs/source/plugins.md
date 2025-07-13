# Plugin Execution Order

Plugins are executed in the order they are registered. The `PluginRegistry`
stores plugins in an `OrderedDict` so iteration yields them in exactly the
same sequence in which they were added. Both `get_plugins_for_stage()` and
`list_plugins()` return plugins in registration order, guaranteeing
deterministic execution whenever multiple plugins share a stage.

## LlamaCppInfrastructure

`LlamaCppInfrastructure` manages a local `llama.cpp` server used by
`LLMResource` providers. The plugin launches the server binary and
validates it via the `/health` endpoint.

```yaml
plugins:
  infrastructure:
    llama:
      type: entity.infrastructure.llamacpp:LlamaCppInfrastructure
      binary: ./server
      model: phi3.Q4_K_M
      host: 0.0.0.0
      port: 8080
      args: [--threads, 4]
```

