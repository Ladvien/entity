# SPIKE-CORE-002: Registry Implementation Comparison

This spike documents how three registry-related components interact in the current codebase:
`ClassRegistry`, `ResourceContainer`, and the older `ResourceRegistry` concept.  The goal is to
clarify their responsibilities and when each is used.

## Components

### ClassRegistry
- Lives in `src/pipeline/initializer.py`.
- Stores plugin classes and configuration **before** any instantiation occurs.
- Provides helper methods `resource_classes()`, `tool_classes()`, and
  `non_resource_non_tool_classes()` for later phases.
- Used by `SystemInitializer` to validate dependencies and build the runtime graph.

### ResourceContainer
- Located in `src/pipeline/resources/container.py`.
- Manages **live resource objects** such as databases or vector stores.
- Supports dependency injection via `register()` and `build_all()` which resolve
  dependencies in a deterministic order using `DependencyGraph`.
- Offers optional connection pools through `add_pool()` and exposes metrics via
  `get_metrics()`.
- Acts as an async context manager ensuring resources are initialized and shut
  down properly.

### ResourceRegistry (legacy)
- Mentioned in early discussions but largely replaced by `ResourceContainer`.
- Served a similar purpose: keeping track of instantiated resources.
- Current code paths reference `ResourceContainer` instead, so "ResourceRegistry"
  can be viewed as an older naming convention.

## Lifecycle Overview
1. **Configuration parsing** – `SystemInitializer` loads YAML/JSON and
   registers plugin classes with `ClassRegistry`.
2. **Dependency validation** – Each plugin class validates its own config and
   declared dependencies using `ClassRegistry`.
3. **Resource build phase** – `ResourceContainer` instantiates concrete
   resources and injects dependencies before pipeline start.
4. **Runtime usage** – Plugins and tools acquire resources from the container or
   from defined resource pools.
5. **Shutdown** – When the application exits, the container shuts down all
   resources in reverse order.

## Usage Diagram
```mermaid
flowchart TD
    subgraph Initialization
        A[Parse config] --> B[ClassRegistry collects plugin classes]
        B --> C[Validate dependencies]
        C --> D[Create ResourceContainer]
        D --> E[build_all() to instantiate resources]
    end
    subgraph Runtime
        F[Plugins / Tools] -- acquire --> G(ResourceContainer)
        G -- release --> F
    end
    Initialization --> Runtime
```

## Observations
- `ClassRegistry` exists only during startup and holds class references.
- `ResourceContainer` persists for the life of the agent and exposes a small API
  (`acquire`, `release`, `get`).
- The deprecated `ResourceRegistry` concept has no direct implementation but the
  name appears in some documentation.  `ResourceContainer` now fulfills that role.

## Recommendation
Continue using `ClassRegistry` for early validation and `ResourceContainer` for
runtime management. Retire remaining mentions of `ResourceRegistry` to avoid
confusion.
