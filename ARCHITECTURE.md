# Architecture Decisions Summary

The following architecture decisions were made through systematic analysis of the Entity Pipeline Framework to optimize for developer adoption, scalability, and maintainability.

Ensure to check `CONTRIBUTING.md` for general contribution guidelines and `ARCHITECTURE.md` for detailed architectural decisions.

## 0. Folder Structure and Naming Conventions

## Repository Layout

Folder structure:
```plaintext
entity/
├── user_plugins/              # Example or custom plugins for local use or sharing
│
├── src/
│   └── entity/                # Main Python package
│       ├── core/              # Core execution engine and orchestration logic
│       ├── plugins/           # Plugin definitions grouped by type
│       ├── resources/         # Composed resource interfaces (memory, storage, llm)
│       ├── config/             # Configuration models and validation logic
│       ├── cli/               # Developer CLI tools and utilities
│       └── utils/             # Misc shared utilities (logging, retries, etc.)
│
└── tests/                     # Unit and integration tests
    ├── test_core/             # Tests for pipeline, agent, and context
    ├── test_plugins/          # Tests for plugin behaviors and base classes
    ├── test_resources/        # Tests for memory, storage, and LLM resources
    ├── test_config/            # Tests for config model parsing and validation
    └── test_cli/              # Tests for CLI commands and developer tools
```

## **1. Core Mental Model: Plugin Taxonomy and Architecture**: Introduces the unified plugin system, plugin categories, lifecycle phases, resource composition, and execution model.

## **2. Progressive Disclosure: Enhanced 3-Layer Plugin System**: Explains the tiered plugin abstraction (decorators, classes, advanced access) with a guided path for increasing plugin complexity.

## **3. Resource Management: Core Canonical + Simple Flexible Keys**: Outlines a hybrid strategy for naming and accessing resources with both standard and custom keys for configuration flexibility.

## **4. Plugin Stage Assignment: Guided Explicit Declaration with Smart Defaults**: Details how plugins are assigned to pipeline stages via explicit declarations, type defaults, and smart tooling.

## **5. Error Handling and Validation: Fail-Fast with Multi-Layered Validation**: Defines a three-phase validation model with circuit breakers to ensure system reliability and fast failure detection.

## **6. Scalability Architecture: Stateless Workers with External State**: Describes the stateless design of pipeline workers and how memory is loaded/saved via external resources for horizontal scaling.

## **7. Response Termination Control**: Restricts response finalization to DELIVER-stage plugins to enforce orderly pipeline execution and prevent premature termination.

## **8. Stage Results Accumulation Pattern**: Establishes methods (`store`, `load`, `has`) for sharing state between stages and iterations to support modular, traceable logic.

## **9. Tool Execution Patterns**: Supports immediate and deferred tool calls using `tool_use()` and `queue_tool_use()` to enable serial and parallel processing.

## **10. Memory Resource Consolidation**: Merges separate memory components into a single `Memory` resource with unified interfaces for key-value, conversation, and vector search.

## **11. Resource Dependency Injection Pattern**: Enforces explicit dependency declarations and container-based injection to validate and control system architecture.

## **12. Plugin Stage Assignment Precedence**: Lists the rules of precedence for determining plugin execution stages, favoring explicit over inferred stage declarations.

## **13. Resource Lifecycle Management**: Mandates strict, ordered initialization and shutdown of resources to prevent partial failures and ensure determinism.

## **14. Configuration Hot-Reload Scope**: Limits hot-reload to parameter changes only, requiring restarts for structural changes to maintain system stability and consistency.

## **15. Error Handling and Failure Propagation**: Implements fail-fast stage-level error handling that triggers recovery via dedicated ERROR-stage plugins.

## **16. Pipeline State Management Strategy**: Uses structured logging and memory persistence to replace snapshot files, supporting observability and clean architecture.

## **17. Plugin Execution Order Simplification**: Executes plugins in the order listed in YAML config, removing complex priority logic for simplicity and predictability.

## **18. Agent and AgentBuilder Separation**: Distinguishes between programmatic (`AgentBuilder`) and config-driven (`Agent`) agent instantiation for clarity and testability.

## **19. Configuration Validation Consolidation**: Standardizes configuration validation using Pydantic models, improving type safety, debugging, and consistency.

## **20. Reasoning Pattern Abstraction Strategy**: Provides built-in reasoning plugins (e.g., Chain of Thought, ReAct) while allowing full extensibility for custom logic.

## **21. Memory Architecture: Primitive Resources + Custom Plugins**: Supplies core memory primitives through a unified resource, encouraging user-defined memory patterns via plugins.

## **22. Tool Discovery Architecture: Lightweight Registry Query + Plugin-Level Orchestration**: Enables lightweight, secure tool discovery via plugin-controlled registry queries and orchestration logic.

## **23. Architectural Decisions not Reviewed**: Lists architectural areas (e.g., logging, telemetry, plugin separation) that have not yet been formally evaluated.


## Architectural Decisions not Reviewed
- Logging
- Docker
- .env credential interpolation
- `ConversationHistory` data schema
- `MetricsCollector` and telemetry
- `core` versus `community` plugin separation
- Import paths / circular imports