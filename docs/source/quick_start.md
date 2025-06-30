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

### Enabling the Ollama Resource
Add the Ollama LLM resource to your configuration so plugins can use it:

```yaml
plugins:
  resources:
    ollama:
      type: ollama_llm
      base_url: "http://localhost:11434"
      model: "tinyllama"
```

The development environment does not require authentication.
Copy `.env.example` to `.env` and update the variables to quickly
configure database and LLM credentials. These values will be automatically
loaded when running the agent or tests.
This fast path aligns with the **15-Minute Rule (2)**, giving new
contributors a working agent almost immediately.
