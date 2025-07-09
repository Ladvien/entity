# Developer Examples

A number of small scripts under the `user_plugins/examples/` directory demonstrate how to
extend and deploy the framework. Each example reads credentials from environment
variables as described in [`user_plugins/examples/README.md`](../../user_plugins/examples/README.md).

- `pipelines/pipeline_example.py` – basic end-to-end pipeline.
- `pipelines/vector_memory_pipeline.py` – shows vector storage integration.
- `tools/search_weather_example.py` – combines built-in search and weather tools.
- `servers/cli_adapter.py` – exposes an agent via the command line interface.

Run an example with Poetry:

```bash
poetry run python user_plugins/examples/pipelines/pipeline_example.py
```

These scripts are useful references when creating your own plugins or adapting
the project to new environments.


