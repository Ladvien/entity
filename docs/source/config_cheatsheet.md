# Configuration Cheat Sheet

Minimal YAML layout for a working agent.

```yaml
entity:
  entity_id: "demo"
  name: "Demo Agent"

plugins:
  resources:
    database:
      type: pipeline.plugins.resources.sqlite_storage:SQLiteStorage
      path: ./entity.db
    llm:
      provider: openai
      model: gpt-4
  tools:
    search:
      type: pipeline.plugins.tools.search:SearchTool
  prompts:
    main:
      type: pipeline.plugins.prompts.simple:SimplePrompt
  adapters:
    http:
      type: pipeline.plugins.adapters.http:HTTPAdapter
```

Use `entity src/cli.py --config config.yaml` to start the agent.
