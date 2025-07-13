# Error Handling and Validation

Entity performs validation in three distinct phases to surface issues early:

1. **Phase 1 – Syntax Validation**
   - Runs in under 100&nbsp;ms.
   - Checks configuration syntax, plugin structure, and obvious conflicts.
2. **Phase 2 – Dependency Validation**
   - Completes in less than one second.
   - Ensures resources exist, detects circular dependencies, and verifies versions.
3. **Phase 3 – Runtime Validation**
   - Occurs in the background after startup.
   - Confirms database connections and external API reachability.

Circuit breakers prevent cascading failures. The framework uses these defaults:

| Resource Type    | Failures to Open | Reset Timeout (s) |
|------------------|-----------------|------------------|
| Databases        | 3               | 30               |
| External APIs    | 5               | 60               |
| File Systems     | 2               | 15               |

Use the CLI to run validations at any time:

```bash
poetry run entity-cli validate --config config/dev.yaml
```

This command executes Phases&nbsp;1 and&nbsp;2 and reports any problems before the pipeline starts.

### Stage Mismatch Warnings

By default the initializer only logs a warning when a plugin's configured stages
override those declared on the class. The warning message reads:
``MyPlugin configured stages [REVIEW] override class stages [DO]``.
Run the CLI with ``--strict-stages`` to escalate these warnings into errors.

## Tuning Circuit Breaker Thresholds

You can override defaults in your configuration:

```yaml
plugins:
  - db:
      type: Postgres
      failure_threshold: 5
      failure_reset_timeout: 120
      init_failure_threshold: 2
```

Lower thresholds provide rapid feedback during development. Production deployments typically use higher limits.
