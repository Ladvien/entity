# Entity Pipeline Framework

Entity is a plugin-based framework for building AI agents. Each agent runs through a fixed set of pipeline stages and can be extended with custom plugins. The framework ships with sensible defaults so you can start quickly and scale to complex deployments.

## Quick Start

```bash
poetry install --with dev
poetry run entity-cli --config config.yaml
```

The CLI loads plugins defined in the YAML file and executes the pipeline for each message.

## Pipeline at a Glance

The architecture uses explicit stages to keep behavior predictable:

1. **PARSE** – validate input and load context
2. **THINK** – reason and plan
3. **DO** – execute tools and actions
4. **REVIEW** – verify responses
5. **DELIVER** – send output
6. **ERROR** – handle failures

Stages repeat until a DELIVER plugin sets a response or the iteration limit is reached.

## Plugin Types

All extensions inherit from `Plugin`. Major categories include:

- **ResourcePlugins** – provide services such as LLMs, databases or file storage.
- **PromptPlugins** – implement reasoning logic using language models.
- **ToolPlugins** – call external APIs or run functions.
- **AdapterPlugins** – convert input and output formats.
- **FailurePlugins** – produce user friendly errors.

ResourcePlugins initialize once at startup, while processing plugins run for each request.

## Resources

Every pipeline has access to three standard resources:

- `llm` – composed from one or more LLM providers.
- `memory` – conversation and key-value storage.
- `storage` – file storage backend.

You can register additional resources or override these defaults in the YAML configuration.

## Configuration Overview

Plugins are listed by stage in the configuration file. The order in the file is the execution order. Explicit `stages` declarations override type defaults and auto classification.

```yaml
plugins:
  resources:
    llm:
      provider: openai
      model: gpt-4
  prompts:
    summarizer:
      type: my_plugins.SummarizePrompt
      stages: [think]
```

## Developing Plugins

Use the provided CLI utilities to generate and analyze plugins:

```bash
poetry run python src/cli/plugin_tool.py generate my_plugin --type prompt
poetry run python src/cli/plugin_tool.py analyze-plugin user_plugins/my_plugin.py
```

These tools help assign the correct stage and validate dependencies.

## Learn More

The [ARCHITECTURE.md](ARCHITECTURE.md) document contains the full design rationale, including plugin lifecycle, dependency injection, and the progressive disclosure model.
