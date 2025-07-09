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
Here is the architecture directory.  Below are references to architectural notes found in `ARCHITECTURE.md`.  Please grep the `ARCHITECTURE.md` file for the section titles to find the full text.  To find the architectural notes, search for the section titles below in `ARCHITECTURE.md`:

```
grep '^## <NUM>\. ' ARCHITECTURE.md
```

The `<NUM>` is the number in the section title above, e.g. `## 1. Core Mental Model: Plugin Taxonomy and Architecture` is section 1.
Absolutely. Here’s your architecture decision summary reformatted to your requested style:

---

## 0. Folder Structure and Naming Conventions – Defines the project’s directory layout and explains the purpose of each top-level folder and submodule.

## 1. Core Mental Model: Plugin Taxonomy and Architecture – Introduces the unified plugin base class and explains the major plugin types, lifecycle phases, and resource composition.
## 2. Progressive Disclosure: Enhanced 3-Layer Plugin System – Describes the plugin abstraction tiers (decorators, classes, advanced) and how developers can gradually increase complexity.
## 3. Resource Management: Core Canonical + Simple Flexible Keys – Balances simplicity and flexibility by supporting both standard (`llm`, `memory`) and custom resource keys in configuration.
## 4. Plugin Stage Assignment: Guided Explicit Declaration with Smart Defaults – Explains how plugin execution stages are assigned via explicit config, class type defaults, and interactive guidance.
## 5. Error Handling and Validation: Fail-Fast with Multi-Layered Validation – Uses a three-phase validation system with circuit breakers to catch configuration, dependency, and runtime issues early.
## 6. Scalability Architecture: Stateless Workers with External State – Implements stateless pipeline workers that load and persist conversation state externally for horizontal scalability.
## 7. Response Termination Control – Restricts response finalization to `DELIVER` stage plugins to enforce complete, predictable pipeline execution.
## 8. Stage Results Accumulation Pattern – Provides `store`, `load`, and `has` methods for inter-stage data sharing, supporting modular design and traceable state flow.
## 9. Tool Execution Patterns – Supports both immediate (`tool_use`) and queued (`queue_tool_use`) tool invocation models to balance synchronous and parallel workflows.
## 10. Memory Resource Consolidation – Merges conversation history, vector search, and key-value store into a single `Memory` resource for simplicity and consistency.
## 11. Resource Dependency Injection Pattern – Uses explicit dependency declarations and container-based injection for testability, validation, and orchestration.
## 12. Plugin Stage Assignment Precedence – Establishes a strict hierarchy for stage assignment: explicit config > plugin type defaults > function auto-classification.
## 13. Resource Lifecycle Management – Enforces topological ordering and fail-fast initialization to ensure resources are fully ready or the system halts cleanly.
## 14. Configuration Hot-Reload Scope – Allows hot-reloading of config parameters only, while structural changes require full restart to avoid unpredictable behavior.
## 15. Error Handling and Failure Propagation – Implements fail-fast stage-level error termination and ERROR-stage fallback plugins for graceful degradation and recovery.
## 16. Pipeline State Management Strategy – Replaces state snapshots with structured logs and memory persistence to simplify debugging and reduce architecture complexity.
## 17. Plugin Execution Order Simplification – Executes plugins in the YAML-listed order, removing the need for priority attributes and improving clarity.
## 18. Agent and AgentBuilder Separation – Separates config-driven `Agent` from programmatic `AgentBuilder` to simplify development and testing responsibilities.
## 19. Configuration Validation Consolidation – Standardizes on Pydantic models for all configuration validation, eliminating JSON Schema and improving type safety.
## 20. Reasoning Pattern Abstraction Strategy – Provides built-in reasoning plugins (e.g., CoT, ReAct) while supporting fully custom logic for advanced use cases.
## 21. Memory Architecture: Primitive Resources + Custom Plugins – Encourages users to build domain-specific memory plugins using the core unified `Memory` resource.
## 22. Tool Discovery Architecture: Lightweight Registry Query + Plugin-Level Orchestration – Allows tool discovery through filtered registry queries, leaving orchestration logic to plugins.
## 23. Plugin System Architecture: Explicit Configuration with Smart Defaults – Promotes explicit configuration with fallback defaults for simplicity and auditability.
## 24. State Management Consolidation: Unified Cache/Memory Pattern – Replaces fragmented state APIs with intuitive verbs like `cache`, `remember`, and `say` for clarity and simplicity.
## 25. Agent Instantiation Unification: Single Agent Class Pattern – Unifies `Agent`, `AgentBuilder`, and `AgentRuntime` into a single `Agent` interface with multiple construction methods.
## 26. Workflow Objects with Progressive Complexity – Introduces Workflow objects to define simple stage-to-plugin mappings that can grow into rich logic over time.
## 27. Workflow Objects: Composable Agent Blueprints – Separates workflow behavior from pipeline execution, enabling reuse, testing, and environment-specific configurations.
