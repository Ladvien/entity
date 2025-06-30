
```{include} ../../README.md
:relative-images:
:start-after: <!-- start quick_start -->
:end-before: <!-- end quick_start -->
```

## Examples

- [`vector_memory_pipeline.py`](../../examples/vector_memory_pipeline.py)
  demonstrates using Postgres, an Ollama LLM, and simple vector memory.

## Runtime Configuration Reload

Reload plugin configuration on the fly:

```bash
python -m src.cli reload-config updated.yaml
```

This feature highlights **Dynamic Configuration Updates** and keeps
long-running agents responsive.

```{toctree}
:hidden:

quick_start
config
context
advanced_usage
principle_checklist
apidocs/index
```

