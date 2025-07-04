# ADR 0001: Core Architecture

The Entity Pipeline framework relies on a plugin based pipeline. Each request flows through explicit stages controlled by registered plugins. Resources, tools and prompts are managed via registries so behavior can be reconfigured without code changes.

## Decision

We adopted a single execution pipeline with fail fast validation. Plugins declare their stage and dependencies up front. The initializer verifies configuration before any runtime work is performed.

## Consequences

* Clear stage boundaries make reasoning about execution simple.
* Swapping plugins or resources only requires configuration changes.
* Initialization fails early when dependencies or configuration are invalid.
