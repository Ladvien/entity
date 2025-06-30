# Entity Pipeline Framework Architecture Summary

When instantiated without a configuration file, ``Agent`` loads a basic set of
plugins so the pipeline can run out of the box:

- ``EchoLLMResource`` – minimal LLM resource that simply echoes prompts.
- ``SimpleMemoryResource`` – in-memory storage available across pipeline runs.
- ``SearchTool`` – wrapper around DuckDuckGo's search API.
- ``CalculatorTool`` – safe evaluator for arithmetic expressions.
- ``HTTPAdapter`` – FastAPI adapter exposing a ``POST /`` endpoint.

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
