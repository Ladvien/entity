# Component Overview

This page explains the main building blocks of the Entity Pipeline framework. Use it alongside the [architecture overview](../../architecture/overview.md), [plugin guide](plugin_guide.md) and [plugin cheat sheet](plugin_cheatsheet.md). A working configuration is available in [`config/dev.yaml`](../../config/dev.yaml).

## Pipelines and Stages

A pipeline is a fixed sequence of stages that an agent runs on each request:

1. **parse** – validate input and load context
2. **think** – plan and reason about actions
3. **do** – execute tools and external calls
4. **review** – check results and format a response
5. **deliver** – send output back to the user
6. **error** – handle failures gracefully

Each stage is independent, making the agent's behavior easier to reason about.

## Plugins

Plugins implement the work at each stage. They interact with the system through `PluginContext` and may use resources or tools. See the [Plugin Guide](plugin_guide.md) for implementation details.

## Plugin Categories

Plugins fall into five groups:

- **Resource** – provide infrastructure like databases or LLMs
- **Tool** – perform discrete actions such as search or calculations
- **Prompt** – manage reasoning strategies and memory
- **Adapter** – expose the agent over interfaces like HTTP or CLI
- **Failure** – format and log error messages

Mix and match plugins to create custom agents. See the [plugin cheat sheet](plugin_cheatsheet.md) for class names and examples.

## Resources

Resources supply shared functionality and are registered by name. Retrieve them in plugins with `context.get_resource("name")`.

### LLM

An LLM resource wraps a language model provider. Plugins can call `context.ask_llm()` to generate text or embeddings.

### Memory vs Storage

`MemoryResource` stores conversation history and vectors persistently. `StorageResource` handles file CRUD across databases, vector stores, and file systems.

## Adapters

Adapters expose the agent to the outside world. The HTTP adapter provides REST endpoints while the CLI adapter runs the agent interactively. Adapters typically run during the `deliver` stage.

### Deliver-stage adapters

Multiple adapters may run during the `deliver` stage. Each adapter receives the pipeline response sequentially, which allows combining behaviors. A common pattern is to send an HTTP reply while also logging the request using `LoggingAdapter`. Register every adapter in the configuration and they will be invoked one after another.

## Putting It Together

Pipelines, plugins, and adapters form the execution engine. Resources supply capabilities like LLMs, memory, and storage. The [architecture document](../../architecture/overview.md) shows how these pieces fit together.
