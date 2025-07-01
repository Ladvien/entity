```{include} ../../README.md
:relative-images:
:start-after: <!-- start quick_start -->
:end-before: <!-- end quick_start -->
```

### CLI Usage
Run an agent from a YAML configuration file:

```bash
python src/cli.py --config config.yml
```

### Using the SearchTool
Register `SearchTool` and call it from your plugin:

```python
from entity.tools import SearchTool

agent.tool_registry.add("search", SearchTool())

@agent.plugin
async def lookup(context):
    return await context.use_tool("search", query="Entity Pipeline")
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
```

The development environment does not require authentication.
Copy `.env.example` to `.env` and update the variables to quickly
configure database and LLM credentials. These values will be automatically
loaded when running the agent or tests.
This fast path aligns with the **15-Minute Rule (2)**, giving new
contributors a working agent almost immediately.

### Runtime Configuration Reload
Reload plugin definitions while the agent is running:

```bash
python src/cli.py reload-config updated.yaml
```

For more on dynamic configuration, see [ARCHITECTURE.md](../../ARCHITECTURE.md#%F0%9F%94%84-reconfigurable-agent-infrastructure).

### Using the "llm" Resource Key
Configure a shared LLM resource in YAML:

```yaml
plugins:
  resources:
    llm:
      type: openai_llm
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
```
