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
      type: user_plugins.prompts.simple:SimplePrompt
  adapters:
    http:
      type: plugins.builtin.adapters.http:HTTPAdapter
    cli:
      type: plugins.builtin.adapters.cli:CLIAdapter
    logging:
      type: plugins.builtin.adapters.logging:LoggingAdapter
```

Use `poetry run python src/cli.py --config config.yaml` to start the agent.
This example references a plugin under the `user_plugins` package to
demonstrate how custom modules can be loaded.
