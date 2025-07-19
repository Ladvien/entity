# Kitchen Sink Agent

This story runs a small ReAct loop using the calculator tool. Thoughts are stored
with `ctx.think()` and reviewed later with `ctx.reflect()` to produce the final
answer.

```bash
poetry run python examples/kitchen_sink/main.py
```
