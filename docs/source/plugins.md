# Plugin Execution Order

Plugins are executed in the order they are registered. The `PluginRegistry`
stores plugins in an `OrderedDict` so iteration yields them in exactly the
same sequence in which they were added. Both `get_plugins_for_stage()` and
`list_plugins()` return plugins in registration order, guaranteeing
deterministic execution whenever multiple plugins share a stage.

<<<<<<< HEAD

## LlamaCppInfrastructure

The `LlamaCppInfrastructure` plugin runs a local [llama.cpp](https://github.com/ggerganov/llama.cpp) server. Configure the binary path and model file:

```yaml
infrastructure:
  llm:
    type: entity.infrastructure.llamacpp.LlamaCppInfrastructure
    binary: /usr/local/bin/llama
    model: /models/mistral-q4.bin
    host: 127.0.0.1
    port: 8080
    args: ["--threads", "4"]
```

Register the plugin in your workflow or resource container like any other infrastructure plugin.
=======
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

>>>>>>> pr-1480
