# Example Scripts

This folder contains small programs that showcase different features of the
Entity pipeline framework. Run them with ``python -m examples.<script>`` from
the repository root or install the project in editable mode with
``pip install -e .``. Installing this way adds the ``src`` directory to your
``PYTHONPATH`` so modules resolve properly.
Most examples read ``config/dev.yaml`` for local runs. Swap in
``config/prod.yaml`` to exercise the same workflow in production.
Many scripts read credentials from environment variables. Copy `.env.example` to
`.env` and fill in the values before running them.

## Variables by Example

| Example | Required Variables |
|---------|-------------------|
| `pipelines/pipeline_example.py` | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| `pipelines/vector_memory_pipeline.py` | `DB_HOST`, `DB_USERNAME`, `DB_PASSWORD`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| `tools/search_weather_example.py` | `WEATHER_API_KEY` |

All other examples work without additional configuration.
