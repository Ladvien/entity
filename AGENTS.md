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

## 0. Folder Structure and Naming Conventions
## 1. Core Mental Model: Plugin Taxonomy and Architecture
## 2. Progressive Disclosure: Enhanced 3-Layer Plugin System
## 3. Resource Management: Core Canonical + Simple Flexible Keys
## 4. Plugin Stage Assignment: Guided Explicit Declaration with Smart Defaults
## 5. Error Handling and Validation: Fail-Fast with Multi-Layered Validation
## 6. Scalability Architecture: Stateless Workers with External State
## 7. Response Termination Control
## 8. Stage Results Accumulation Pattern
## 9. Memory Resource Consolidation
## 10. Resource Dependency Injection Pattern
## 11. Plugin Stage Assignment Precedence
## 12. Resource Lifecycle Management
## 13. Configuration Hot-Reload Scope
## 14. Error Handling and Failure Propagation
## 15. Pipeline State Management Strategy
## 16. Plugin Execution Order Simplification
## 17. Agent and AgentBuilder Separation
## 18. Configuration Validation Consolidation
## 19. Reasoning Pattern Abstraction Strategy
## 20. Memory Architecture: Primitive Resources + Custom Plugins
## 21. Tool Discovery Architecture: Lightweight Registry Query + Plugin-Level Orchestration
## 22. Plugin System Architecture: Explicit Configuration with Smart Defaults
## 23. State Management Consolidation: Unified Cache/Memory Pattern
## 24. Agent Instantiation Unification: Single Agent Class Pattern
