# Configuration Cheat Sheet

Minimal YAML layout for a working agent.

```yaml
server:
  host: "0.0.0.0"
  port: 8000

workflow:
  parse: [http]
  think: [main]
  deliver: [http]

plugins:
  resources:
    database:
      type: plugins.builtin.resources.sqlite_storage:SQLiteStorageResource
      path: ./entity.db
    llm:
      provider: openai
      model: gpt-4
  prompts:
    main:
      type: user_plugins.prompts.simple:SimplePrompt
  adapters:
    http:
      type: plugins.builtin.adapters.http:HTTPAdapter
      stages: [parse, deliver]
```

Use `poetry run entity-cli --config config.yaml` to start the agent.
This example references a plugin under the `user_plugins` package to
show how custom modules can be loaded.
