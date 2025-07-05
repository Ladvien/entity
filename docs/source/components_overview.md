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
