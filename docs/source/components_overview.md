<<<<<<< HEAD
# Component Overview

This page summarizes the core building blocks of Entity pipelines. For diagrams and a deeper discussion see [Architecture](architecture.md) and the [Plugin Guide](plugin_guide.md). A working configuration can be found in [`config/dev.yaml`](../../config/dev.yaml).

## Pipelines

A *pipeline* orchestrates execution across explicit stages like `parse`, `think` and `do`. Each stage runs its registered plugins in order. Pipelines enforce clear boundaries so behaviors remain predictable and easy to reason about.

## Plugins

Plugins implement the logic for each stage. They interact with the system through `PluginContext` and may use resources or tools. Refer to the [Plugin Guide](plugin_guide.md) for implementation details and examples.

## Adapters

Adapters expose a pipeline through some interface such as CLI, WebSocket or gRPC. They translate external requests into pipeline calls and return the responses.

## Resources

Resources provide shared functionality like databases, LLM access and file storage. They are registered by name in the configuration and retrieved in plugins via `context.get_resource()`.

### LLM

An LLM resource wraps a large language model provider. Plugins can call `context.ask_llm()` to generate text or embeddings without caring about the underlying API.

### Memory vs Storage

`MemoryResource` keeps conversation history in memory only. It is *ephemeral* and lost when the process stops. `StorageResource` persists history and files using databases, vector stores and file systems. It survives restarts and can combine several backends behind one interface.

## Putting It Together

Pipelines, plugins and adapters form the execution engine. Resources supply capabilities like LLMs, memory and long‑term storage. The [architecture document](architecture.md) shows how these pieces fit together.
=======
# Components Overview

This page explains the main building blocks of the Entity Pipeline framework.
Use it alongside the [architecture overview](architecture.md) and the
[plugin cheat sheet](plugin_cheatsheet.md) for quick reference.

## Pipelines and Stages

A pipeline is a fixed sequence of stages that an agent runs through on each
request:

1. **parse** – validate input and load context
2. **think** – plan and reason about actions
3. **do** – execute tools and external calls
4. **review** – check results and format a response
5. **deliver** – send output back to the user
6. **error** – handle failures gracefully

Each stage is independent, making it easy to reason about the agent's behavior.

## Plugin Categories

Plugins implement the work at each stage and fall into five categories:

- **Resource** – provide infrastructure like databases or LLMs
- **Tool** – perform discrete actions such as search or calculations
- **Prompt** – manage reasoning strategies and memory
- **Adapter** – expose the agent over interfaces like HTTP or CLI
- **Failure** – format and log error messages

You can mix and match plugins to create custom agents.
See the [plugin cheat sheet](plugin_cheatsheet.md) for class names and examples.

## Core Resources

Resources are stateful services registered by name. The framework includes:

- **`LLMResource`** – wraps a language model backend
- **`MemoryResource`** – stores conversation history or embeddings
- **`StorageResource`** – handles databases and file storage

Resources are retrieved inside plugins via `context.get_resource("name")`.

## Adapters

Adapters make the agent accessible to the outside world. For example,
the HTTP adapter exposes REST endpoints, while the CLI adapter runs the
agent interactively. Adapters are plugins that typically run during the
`deliver` stage to send responses back to the caller.

Combining these components lets you build reusable and predictable agents.
>>>>>>> 8d0c270bb5e3d80688ec98972bcaf6729a41b4ce
