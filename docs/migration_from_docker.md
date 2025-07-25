# Migrating from Docker

Earlier versions recommended running `docker compose up` before using the framework.
Local execution no longer requires these containers.

1. Stop any running compose stack with `docker compose down -v`.
2. Run your agent scripts directly. `load_defaults()` will create a DuckDB database and local storage automatically.
3. Only start `docker compose` again when you need Postgres or Ollama for production or integration tests.
