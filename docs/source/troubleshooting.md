# Troubleshooting

## Initialization failures
- **Invalid plugin path** – ensure each plugin `type` is a full import path.
- **Missing environment variable** – check `${VAR}` placeholders in YAML and your `.env` file.
- **Circular dependency detected** – review plugin `dependencies` for cycles.

## Dependency validation errors
- **Plugin requires a resource not registered** – confirm that all names in `dependencies` exist under `plugins:` in the config file.
- **Config validation failed** – run `poetry run entity-cli --config your.yaml` to see detailed messages.

If initialization still fails, enable debug logging with `LOG_LEVEL=DEBUG` when running the validator for verbose output.

## Runtime errors
- **No response generated** – verify each stage sets the pipeline response or passes control to the next stage.
- **Tool not found** – make sure the tool is registered in `tool_registry` and that the calling plugin uses the correct name.
- **Plugin failed to import** – confirm the module path and that the file is in your `PYTHONPATH`.

## Docker issues
- **Container exits immediately** – check the command in your `Dockerfile` and ensure the configuration file path is correct.
- **Ports not exposed** – run the container with `-p 8000:8000` so the HTTP adapter is reachable from the host.

