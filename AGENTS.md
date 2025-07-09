# Entity Pipeline Contributor Guide

This repository contains a plugin based framework for building AI agents.
Use this document when preparing changes or reviewing pull requests.

## Important Notes
- **You must adhere to architectural guidelines when making changes.** See
  `ARCHITECTURE.md` for details on the architectural design and principles.
- Refer to `CONTRIBUTING.md` for general contribution guidelines.
- The project is pre-alpha; remove unused code rather than keeping
  backward compatibility.
- Prefer adding `TODO:` comments when scope is unclear.
- Always use the Poetry environment for development.
- Run `poetry install --with dev` before executing any quality checks or tests.


## Architecture
Here is the architecture directory.  Below are references to architectural notes found in `ARCHITECTURE.md`.  Please grep the `ARCHITECTURE.md` file for the section titles to find the full text. 

* **1. Core Mental Model: Plugin Taxonomy and Architecture**: Describes the foundational plugin architecture of the framework, including plugin categories, resource composition, lifecycle management, and development patterns.

* **2. Progressive Disclosure: Enhanced 3-Layer Plugin System**: Explains the framework’s tiered plugin abstraction model and how developers progressively adopt complexity through decorators, classes, and advanced customization.

* **3. Resource Management: Core Canonical + Simple Flexible Keys**: Details the hybrid naming strategy for resource access, supporting both simple canonical names and flexible custom keys for more complex setups.

* **4. Plugin Stage Assignment: Guided Explicit Declaration with Smart Defaults**: Describes how plugins are assigned to pipeline stages using explicit declarations, smart defaults, and tooling guidance to reduce developer confusion.

* **5. Error Handling and Validation: Fail-Fast with Multi-Layered Validation**: Defines a three-phase validation system for configuration, dependencies, and runtime connectivity to catch issues early and enforce system health.

* **6. Scalability Architecture: Stateless Workers with External State**: Outlines the stateless worker design that enables horizontal scaling by storing all pipeline context in external memory systems.

* **6. Response Termination Control**: Specifies that only plugins in the DELIVER stage can finalize the response, ensuring consistent and complete pipeline processing.

* **7. Stage Results Accumulation Pattern**: Explains how stages communicate via an internal key-value store (`context.store`, `context.load`, `context.has`) to maintain clarity and traceability of pipeline outputs.

* **8. Tool Execution Patterns**: Details support for both immediate and queued tool execution patterns, giving developers control over tool concurrency and performance strategies.

* **9. Memory Resource Consolidation**: Describes the unification of all memory-related responsibilities into a single `Memory` resource, simplifying configuration and access patterns.

* **10. Resource Dependency Injection Pattern**: Covers how resources declare and receive dependencies explicitly, enabling full graph validation, clear architecture, and hot-reload support.

* **11. Plugin Stage Assignment Precedence**: Specifies the order of precedence for determining plugin stage assignments—explicit declarations, plugin type defaults, and auto-classification.

* **12. Resource Lifecycle Management**: Establishes that resources are initialized and shut down in strict topological order, ensuring predictable system startup and teardown behavior.

* **13. Configuration Hot-Reload Scope**: Clarifies which configuration changes can be hot-reloaded (parameters only) versus those requiring full system restarts (structural changes).

* **14. Error Handling and Failure Propagation**: Explains the framework’s fail-fast behavior, where any plugin failure immediately halts stage execution and routes processing to the ERROR stage.

* **15. Pipeline State Management Strategy**: Defines how all conversation persistence and debugging state is managed through structured logs and the memory resource, eliminating separate state snapshot files.

* **16. Plugin Execution Order Simplification**: States that plugins now execute in the order defined in the YAML configuration, removing priority fields for simplicity and predictability.

* **17. Agent and AgentBuilder Separation**: Distinguishes between `Agent` (for config-based instantiation) and `AgentBuilder` (for programmatic construction), promoting clear intent and separation of concerns.

* **18. Configuration Validation Consolidation**: Mandates the exclusive use of Pydantic for configuration validation, replacing JSON Schema and improving type safety, error messages, and tooling support.


## Repository Layout

Folder structure:
```plaintext
entity/
├── user_plugins/                # Example or custom plugins (used by AgentBuilder or CLI)
│   ├── my_prompt.py            # Example PromptPlugin
│   └── my_tool.py              # Example ToolPlugin
│
├── src/
│   └── entity/                 # Main package
│       ├── __init__.py
│       ├── core/               # Core execution engine and orchestration
│       │   ├── __init__.py
│       │   ├── agent.py         # Agent: config-based runner
│       │   ├── builder.py       # AgentBuilder: programmatic plugin composition
│       │   ├── context.py       # PipelineContext: runtime data, resource access, tool calls
│       │   ├── pipeline.py      # PipelineWorker: stage loop executor
│       │   ├── state.py         # PipelineState: transient run state container
│       │   ├── registry.py      # PluginRegistry: maps plugins to pipeline stages
│       │   └── container.py     # DependencyContainer: initializes and wires ResourcePlugins
│       ├── plugins/            # Plugin type definitions and bases
│       │   ├── __init__.py
│       │   ├── base.py              # Plugin ABC: lifecycle and stage contract
│       │   ├── resource_plugin.py   # ResourcePlugin base: systems like LLMs, DBs, memory
│       │   ├── prompt_plugin.py     # PromptPlugin base: THINK stage logic
│       │   ├── tool_plugin.py       # ToolPlugin base: DO stage tools
│       │   ├── adapter_plugin.py    # AdapterPlugin base: input/output for PARSE/DELIVER
│       │   ├── failure_plugin.py    # FailurePlugin base: ERROR stage fallbacks
│       │   └── infra_plugin.py      # InfrastructurePlugin base: metrics, tracing, health
│       ├── resources/          # Composed system resources
│       │   ├── __init__.py
│       │   ├── memory.py          # Unified memory (e.g. history + vector store)
│       │   ├── storage.py         # Filesystem or cloud storage abstraction
│       │   └── llm.py             # Unified LLM interface and access layer
│       ├── config/             # Configuration and validation
│       │   ├── __init__.py
│       │   └── models.py         # Pydantic models for plugin/resource config
│       ├── cli/                # CLI tools for validation, debugging, analysis
│       │   ├── __init__.py
│       │   ├── main.py            # CLI entry point
│       │   ├── validate.py        # Config/schema validator
│       │   ├── analyze_plugin.py  # Suggest stage for user-defined plugin
│       │   └── graph_dep.py       # Resource dependency graph visualizer
│       └── utils/              # Misc shared helpers
│           └── __init__.py
│
└── tests/                     # Unit test suite
    ├── test_core/              # Agent, builder, context, pipeline
    ├── test_plugins/           # Plugin behavior and integration
    ├── test_resources/         # Memory, storage, LLM resource tests
    ├── test_config/            # Config parsing, validation edge cases
    └── test_cli/               # CLI command behavior and error handling
```
