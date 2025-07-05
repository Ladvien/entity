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
