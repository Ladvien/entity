# Logging Workflow Templates

Choose how plugins send log entries. The console template writes readable text, while the JSON template saves structured logs.

## Console Logging

```yaml
workflows:
  console_logger:
    output:
      - entity.plugins.logging.ConsoleLogger
```

## JSON Logging

```yaml
workflows:
  json_logger:
    output:
      - entity.plugins.logging.JsonLogger
```
