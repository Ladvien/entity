# Default Setup Agent

This example uses the high level `Agent` API and the
`@agent.tool` and `@agent.prompt` decorators to register plugins. The
prompt is assigned to the `OUTPUT` stage so responses are emitted from
the correct point in the pipeline.

Run it with:

```bash
poetry run python examples/default_setup/main.py
```
