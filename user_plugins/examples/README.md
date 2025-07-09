# Example Scripts

This folder contains small programs that showcase different features of the Entity pipeline framework.
Run them with ``python -m user_plugins.examples.<script>`` from the repository root or install
the package in editable mode with ``pip install -e .``.
Many scripts read credentials from environment variables. Copy `.env.example` to
`.env` and fill in the values before running them.

## Variables by Example

| Example | Required Variables |
|---------|-------------------|
| `pipelines/pipeline_example.py` | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| `pipelines/vector_memory_pipeline.py` | `DB_HOST`, `DB_USERNAME`, `DB_PASSWORD`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| `tools/search_weather_example.py` | `WEATHER_API_KEY` |

All other examples work without additional configuration.
