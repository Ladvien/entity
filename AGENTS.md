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


## Repository / Folder Structure
```sh
entity/                 # Project root (could also contain README, pyproject.toml, etc.)
├── src/
│   └── entity/         # Main package for the framework
│       ├── __init__.py
│       ├── core/       # Core framework logic (execution engine, context, agent)
│       │   ├── __init__.py
│       │   ├── agent.py            # `Agent` class (config-driven initialization):contentReference[oaicite:0]{index=0}
│       │   ├── builder.py          # `AgentBuilder` class (programmatic agent construction)
│       │   ├── context.py          # Pipeline context (store/load results, get_resource, tool usage)
│       │   ├── pipeline.py         # Pipeline executor/worker (stage loop, stateless execution):contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}
│       │   ├── state.py           # Data structures for pipeline state (e.g. `PipelineState`)
│       │   ├── registry.py         # Plugin registry (manages plugins by stage, YAML order):contentReference[oaicite:5]{index=5}
│       │   └── container.py        # Dependency container for ResourcePlugins (initialization order):contentReference[oaicite:6]{index=6}
│       ├── plugins/    # Plugin definitions, categorized by type (all inherit from Plugin base):contentReference[oaicite:7]{index=7}
│       │   ├── __init__.py         # May import common plugin classes for convenience
│       │   ├── base.py             # Defines `Plugin` ABC base class and shared plugin logic:contentReference[oaicite:8]{index=8}
│       │   ├── resource_plugin.py  # `ResourcePlugin` base class and subclasses (LLMResourcePlugin, etc.):contentReference[oaicite:9]{index=9}
│       │   ├── prompt_plugin.py    # `PromptPlugin` base (LLM reasoning plugins):contentReference[oaicite:10]{index=10}
│       │   ├── tool_plugin.py      # `ToolPlugin` base (external action plugins):contentReference[oaicite:11]{index=11}
│       │   ├── adapter_plugin.py   # `AdapterPlugin` base and I/O plugin classes (InputAdapter, OutputAdapter):contentReference[oaicite:12]{index=12}:contentReference[oaicite:13]{index=13}
│       │   ├── failure_plugin.py   # `FailurePlugin` class (error handling plugins):contentReference[oaicite:14]{index=14}
│       │   └── infra_plugin.py     # `InfrastructurePlugin` class (operational/monitoring plugins):contentReference[oaicite:15]{index=15}
│       ├── resources/  # Core resource classes and composition (unified Memory, Storage, etc.)
│       │   ├── __init__.py
│       │   ├── memory.py           # Unified `Memory` resource (conv. history, key-value store):contentReference[oaicite:16]{index=16}
│       │   ├── storage.py          # `Storage` resource (file systems, etc.)
│       │   └── llm.py              # Unified `LLM` resource (composed from LLM providers, if applicable)
│       ├── config/     # Configuration models and validation
│       │   ├── __init__.py
│       │   └── models.py          # Pydantic models for plugin configs (consolidated):contentReference[oaicite:17]{index=17}:contentReference[oaicite:18]{index=18}
│       ├── cli/        # Command-line interface tools for developers
│       │   ├── __init__.py
│       │   ├── main.py            # CLI entry point (argument parsing, command dispatch)
│       │   ├── validate.py        # CLI command: validate config and plugins:contentReference[oaicite:19]{index=19}
│       │   ├── analyze_plugin.py  # CLI command: analyze plugin function for stage hints:contentReference[oaicite:20]{index=20}
│       │   └── graph_dep.py       # CLI command: visualize dependency graph:contentReference[oaicite:21]{index=21}
│       └── utils/ (optional)      # Misc utilities (e.g., logging setup, common helpers)
│           └── __init__.py 
└── tests/               # Test suite organized parallel to src structure
    ├── test_core/      # Tests for core components (Agent, pipeline, context, etc.)
    ├── test_plugins/   # Tests for plugin base classes and sample plugins
    ├── test_resources/ # Tests for resource initialization and memory persistence
    ├── test_config/    # Tests for config validation (Pydantic models, hot-reload cases)
    └── test_cli/       # Tests for CLI commands and developer tools
```
