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


## Best Practices

- Keep authentication tokens secret and rotate them regularly.
- Validate all user supplied input using the provided utilities.
- Restrict adapter roles to the minimal set required for your deployment.
