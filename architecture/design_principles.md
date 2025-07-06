# Design Principles

The framework follows a few simple rules so agents remain easy to reason about:

1. **Progressive disclosure** – simple tasks stay simple, complex ones remain possible.
2. **Async-first** – predictable ordering with nonblocking execution.
3. **Runtime reconfiguration** – validate and apply changes without restarts.
4. **Clear stage boundaries** – structured logs around each phase.
5. **Single-name resources** – one canonical name per capability.
