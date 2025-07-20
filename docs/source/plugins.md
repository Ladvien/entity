# Plugin Execution Order

Plugins are executed in the order they are registered. The `PluginRegistry`
stores plugins in an `OrderedDict` so iteration yields them in exactly the
same sequence in which they were added. Both `get_plugins_for_stage()` and
`list_plugins()` return plugins in registration order, guaranteeing
deterministic execution whenever multiple plugins share a stage.

Plugins declared in a YAML configuration file maintain this ordering as well.
The initializer reads entries sequentially and registers each plugin as it
appears, so restarting the system with the same YAML file yields identical
execution order. The registry preserves the original sequence for each stage,
ensuring stage-level execution order matches the YAML definition exactly.

## Plugin Lifecycle

Every plugin defines asynchronous `initialize()` and `shutdown()` methods.  The
base :class:`~entity.core.plugins.Plugin` implementation simply tracks lifecycle
state and provides `_on_initialize()` and `_on_shutdown()` hooks.  Subclasses
override these hooks when they need to allocate or release resources.

Repeated calls to `initialize()` or `shutdown()` are ignored, so plugins can be
safely restarted without duplicating work.

## LlamaCppInfrastructure

`LlamaCppInfrastructure` manages a local [llama.cpp](https://github.com/ggerganov/llama.cpp)
server used by `LLMResource` providers. The plugin launches the server binary and
validates it via the `/health` endpoint.

```yaml
plugins:
  infrastructure:
    llama:
      type: entity.infrastructure.llamacpp:LlamaCppInfrastructure
      binary: /usr/local/bin/llama
      model: /models/mistral-q4.bin
      host: 127.0.0.1
      port: 8080
      args: ["--threads", "4"]
```

Register the plugin in your workflow or resource container like any other
infrastructure plugin.

## EchoLLMBackend

`EchoLLMBackend` provides a dummy LLM server used by the default provider. It simply echoes input
back to the caller and exposes the `"llm_backend"` infrastructure type.

```yaml
plugins:
  infrastructure:
    echo_llm_provider:
      type: plugins.builtin.infrastructure.echo_llm_provider:EchoLLMProvider
```

No configuration options are required.

## AsyncPGInfrastructure

`AsyncPGInfrastructure` connects to a PostgreSQL server and exposes a
`database` for resources.

```yaml
plugins:
  infrastructure:
    postgres_backend:
      type: entity.infrastructure.asyncpg:AsyncPGInfrastructure
      dsn: postgresql://user:pass@localhost:5432/agent
```
