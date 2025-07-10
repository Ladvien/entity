# First Pipeline Execution

Run the sample agent created in the previous step.

1. Change into the new directory:

```bash
cd my_agent
```

2. Start the HTTP server:

```bash
python src/main.py
```

3. Send a test message:

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"message": "hello"}' http://localhost:8000/
```

The response comes from the default EchoLLMResource.

Run the DuckDB memory example to see persistence:

```bash
poetry run python examples/duckdb_memory_agent/main.py
```

After running it twice inspect the `agent.duckdb` file:

```bash
duckdb agent.duckdb "SELECT * FROM kv;"
```
