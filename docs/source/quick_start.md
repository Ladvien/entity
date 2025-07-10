```{include} ../../README.md
:relative-images:
:start-after: <!-- start quick_start -->
:end-before: <!-- end quick_start -->
```

### CLI Usage
Run an agent from a YAML configuration file:

```bash
entity-cli --config config.yaml
```

### Programmatic Configuration
Build the same configuration in Python using the models from
`entity.config`:

```python
from entity.config.models import EntityConfig, PluginsSection, PluginConfig

config = EntityConfig(
    workflow={"think": ["main"], "deliver": ["http"]},
    plugins=PluginsSection(
        prompts={"main": PluginConfig(type="user_plugins.prompts.simple:SimplePrompt")},
        adapters={"http": PluginConfig(type="plugins.builtin.adapters.http:HTTPAdapter", stages=["parse", "deliver"])},
        resources={"llm": PluginConfig(provider="openai", model="gpt-4")},
    ),
)
```

### Using the SearchTool
Register `SearchTool` and call it from your plugin:

```python
from user_plugins.tools import SearchTool

agent.tool_registry.add("search", SearchTool())

@agent.plugin
async def lookup(context):
    return await context.tool_use("search", query="Entity Pipeline")
```

The `context` argument is an instance of `PluginContext`. See
[the context guide](context.md) for an overview of its helper methods.

### Configuring the LLM Resource
Select an LLM provider in your configuration. The following example uses
Ollama, but you can set `provider` to `openai`, `gemini`, or `claude`:

```yaml
plugins:
  resources:
    llm:
      provider: ollama  # openai, ollama, gemini, claude
      base_url: "http://localhost:11434"
      model: "tinyllama"
workflow:
  think: []
```

The development environment does not require authentication.
Copy `.env.example` to `.env` and update the variables to quickly
configure database and LLM credentials. These values will be automatically
loaded when running the agent or tests.
This fast path aligns with the **15-Minute Rule (2)**, giving new
contributors a working agent almost immediately.

### Runtime Configuration Reload
Reload parameter values for existing plugins while the agent is running:

```bash
poetry run entity-cli reload-config updated.yaml
```

Only updates to plugin parameters can be reloaded. Structural changes—adding or
removing plugins, changing stage assignments, or altering dependencies—require a
restart. For more on dynamic configuration see the
[architecture overview](https://github.com/Ladvien/entity/blob/main/architecture/general.md#%F0%9F%94%84-reconfigurable-agent-infrastructure).

### Using the "llm" Resource Key
Configure a shared LLM resource in YAML:

```yaml
plugins:
  resources:
    llm:
      provider: openai
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
```

