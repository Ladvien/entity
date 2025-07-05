# Configuration Cheat Sheet

Minimal YAML layout for a working agent.

```yaml
entity:
  entity_id: "demo"
  name: "Demo Agent"

plugins:
  resources:
    database:
      type: plugins.builtin.resources.sqlite_storage:SQLiteStorage
      path: ./entity.db
    llm:
      provider: openai
      model: gpt-4
  tools:
    search:
      type: plugins.builtin.tools.search:SearchTool
  prompts:
    main:
      type: plugins.contrib.prompts.simple:SimplePrompt
  adapters:
    http:
      type: plugins.builtin.adapters.http:HTTPAdapter
```

Use `entity src/cli.py --config config.yaml` to start the agent.
