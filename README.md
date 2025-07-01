# Entity Pipeline Framework Architecture Summary

When instantiated without a configuration file, ``Agent`` loads a basic set of
plugins so the pipeline can run out of the box:

- ``EchoLLMResource`` – minimal LLM resource that simply echoes prompts.
- ``SimpleMemoryResource`` – in-memory storage available across pipeline runs.
- ``SearchTool`` – wrapper around DuckDuckGo's search API.
- ``CalculatorTool`` – safe evaluator for arithmetic expressions.

These defaults allow ``Agent()`` to process messages without any external
configuration.

<!-- start quick_start -->
Get started quickly by installing the package and running an agent with a YAML
file:

```bash
pip install entity-pipeline
python src/cli.py --config config.yaml
```
<!-- end quick_start -->

<!-- start config -->
The ``llm`` resource now accepts a ``provider`` key. Choose from ``openai``,
``ollama``, ``gemini``, or ``claude``:

```yaml
plugins:
  resources:
    llm:
      provider: ollama  # openai, ollama, gemini, claude
      model: tinyllama
      base_url: "http://localhost:11434"
```
<!-- end config -->

Every plugin executes with a ``PluginContext`` which grants controlled
access to resources, conversation history, and helper methods for calling
tools or LLMs. This context keeps plugin logic focused while the framework
handles state management. See the
[context guide](docs/source/context.md) for a detailed overview of its
methods and responsibilities.


To expose the agent over HTTP, build a FastAPI app that uses the agent:

```python
from fastapi import FastAPI
from app import create_app

agent = Agent(...)
app = create_app(agent)
```

## Design Principles in Action

- **Progressive Disclosure (1)**: `Agent()` works out of the box with helpful defaults.
- **Zero Configuration Default (3)**: Basic resources and tools require no YAML.
- **Fail-Fast Validation (15)**: `SystemInitializer` raises clear errors when dependencies are missing.
- **Intuitive Mental Models (21)**: Stages map directly to `Parse`, `Think`, `Do`, `Review`, `Deliver`, and `Error`.


```python
# Progressive Disclosure example
agent = Agent()
@agent.plugin
def hello(context):
    return "hello"
```

## Runtime Configuration Reload
Update plugin settings without restarting the agent.

```bash
python src/cli.py reload-config updated.yaml
```

See [ARCHITECTURE.md](ARCHITECTURE.md#%F0%9F%94%84-reconfigurable-agent-infrastructure) for details on dynamic reconfiguration.

### Using the "llm" Resource Key
Define your LLM once and share it across plugins:

```yaml
plugins:
  resources:
    llm:
      type: openai_llm
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
```
