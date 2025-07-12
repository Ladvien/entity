# Intermediate Agent

This example splits reasoning across stages. The THINK stage stores a
`thought` with `ctx.think()` and the OUTPUT stage retrieves it using
`ctx.reflect()`.

```bash
poetry run python examples/intermediate_agent/main.py
```
