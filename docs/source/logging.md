# Logging Resource

Entity provides a built in `LoggingResource` offering a single async `log()`
interface. It can write to multiple destinations at the same time. The default
configuration prints to the console.

## Usage

Plugins and resources obtain the logger via the context:

```python
logger = context.get_resource("logging")
await logger.log("info", "step starting", component="plugin", pipeline_id=context.pipeline_id)
```

## Configuration Example

```yaml
plugins:
  agent_resources:
    logging:
      type: entity.resources.logging:LoggingResource
      outputs:
        - type: console
        - type: structured_file
          path: ./logs/agent.jsonl
          max_bytes: 10MB
          backup_count: 2
```

`max_bytes` sets the file size threshold for rotation using common size suffixes
like `KB`, `MB`, and `GB`. When the active file exceeds this threshold it is
renamed with a numbered suffix and a new file is created. `backup_count`
controls how many rotated files to keep.

## Automatic Logging

All plugins based on :class:`~entity.core.plugins.BasePlugin` automatically log
the start, success, and failure of their ``execute`` method. Resource classes
derived from :class:`~entity.core.plugins.ResourcePlugin` log each operation
tracked via ``_track_operation``. No additional code is required other than
having a ``LoggingResource`` registered in the system.
