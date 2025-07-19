# Full Workflow Example

This extended story wires together PostgreSQL, pgvector, and multiple LLM providers.
It also enables structured logging and metrics collection to showcase a realistic
production setup.

## Prerequisites

- A running PostgreSQL instance with the `pgvector` extension enabled.
- Environment variables:
  - `POSTGRES_DSN` – connection string for PostgreSQL.
  - `OPENAI_API_KEY` – OpenAI authentication token.
  - `ANTHROPIC_API_KEY` – Anthropic authentication token.
- A local Ollama server (default `http://localhost:11434`).

## Run

```bash
poetry run python examples/full_workflow/main.py
```

Metrics are stored in the built-in collector and logs are printed to the
console.
