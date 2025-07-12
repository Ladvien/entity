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
```
