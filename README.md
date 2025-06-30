# Entity Pipeline Framework Architecture Summary

When instantiated without a configuration file, ``Agent`` loads a basic set of
plugins so the pipeline can run out of the box:

- ``EchoLLMResource`` – minimal LLM resource that simply echoes prompts.
- ``SimpleMemoryResource`` – in-memory storage available across pipeline runs.
- ``SearchTool`` – wrapper around DuckDuckGo's search API.
- ``CalculatorTool`` – safe evaluator for arithmetic expressions.

These defaults allow ``Agent()`` to process messages without any external
configuration.

``Agent`` also accepts keyword arguments for common resources so you can build a
configuration programmatically instead of providing a YAML file:

```python
agent = Agent(
    llm="pipeline.plugins.resources.ollama_llm:OllamaLLMResource",
    database=False,  # disable database resource
    logging={
        "type": "pipeline.plugins.resources.structured_logging:StructuredLogging",
        "file_enabled": False,
    },
)
```

Each argument is converted into the dictionary structure expected by
``SystemInitializer``.

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
