# Security Configuration Guide

This guide outlines the basic security features built into the pipeline.

## Authentication Tokens

Adapters accept a mapping of tokens to allowed roles. For example:

```yaml
plugins:
  adapters:
    http:
      # type: plugins.builtin.adapters.http:HTTPAdapter
      auth_tokens:
        admin-token: ["http"]
```

Each adapter validates the provided bearer token and ensures the role is allowed.

## Input Validation Hooks

Use `StageInputValidator` to register callbacks that inspect or modify the
`PluginContext` before each stage plugin runs. Hooks are registered on the
`SystemRegistries.validators` object.

```python
capabilities.validators.register(PipelineStage.PARSE, my_validator)
```

## Best Practices

- Keep authentication tokens secret and rotate them regularly.
- Validate all user supplied input using the provided utilities.
- Restrict adapter roles to the minimal set required for your deployment.
