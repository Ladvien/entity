# Kitchen Sink Agent

This example demonstrates a ReAct-style loop with the built-in calculator tool.
The THINK stage stores analysis with `ctx.think()` and the OUTPUT stage
returns it using `ctx.reflect()`.

```bash
poetry run python examples/kitchen_sink/main.py
```
