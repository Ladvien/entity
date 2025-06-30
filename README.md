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
