# Production Deployment Guide

This document describes a minimal production setup for running the Entity Pipeline Framework.
It assumes you already tested your configuration locally and want to move it to a
reliable environment. Provide your own `Dockerfile` for building the image.

.. mermaid:: diagrams/deployment_patterns.mmd

## Container Image

Build a Docker image containing your plugins and configuration:

```bash
docker build -t entity-agent:latest .
```

Tag and push the image to your registry of choice. Kubernetes and many PaaS
providers can pull directly from Docker Hub or a private registry.

## Environment Variables

Secrets such as API keys should be provided through environment variables. The
example `config/prod.yaml` expects variables like `OPENAI_API_KEY`. Avoid baking
secrets into the image.

## Process Manager

Run the agent under a process supervisor to handle restarts:

```bash
poetry run entity-cli --config config/prod.yaml
```

Use `systemd` or a container orchestrator such as Kubernetes to keep the process
healthy and to manage logs. Configure liveness probes on the HTTP endpoint so
the orchestrator can restart the container on failures.

## Scaling

For horizontal scaling you can run multiple agent replicas behind a load
balancer. Use a shared database and file store so each instance has access to
conversation history and uploaded files. Enable tracing (see
`monitoring.md`) to gain visibility into resource usage.


