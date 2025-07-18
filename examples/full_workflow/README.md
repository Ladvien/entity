# Full Workflow Example

This example demonstrates how to combine multiple LLM providers with a PostgreSQL
backend and pgvector. It also enables structured logging and metrics
collection.

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
