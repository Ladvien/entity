# Example Scripts

This folder contains small programs that showcase different features of the Entity pipeline framework.
Many of them read credentials from environment variables. Copy `.env.example` to `.env` and fill in the values before running the scripts.

## Variables by Example

| Example | Required Variables |
|---------|-------------------|
| `pipelines/pipeline_example.py` | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| `pipelines/vector_memory_pipeline.py` | `DB_HOST`, `DB_USERNAME`, `DB_PASSWORD`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |
| `tools/search_weather_example.py` | `WEATHER_API_KEY` |

All other examples work without additional configuration.
