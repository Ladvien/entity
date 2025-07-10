# ADR 0003: Five-Minute Start Default

## Status
Accepted

## Context
Early experimentation should require no external services. A persistent database often slows first-time users. DuckDB runs in-process and can operate entirely in memory.

## Decision
The default `memory` resource uses DuckDB in memory so new users can launch an agent with a single command. This configuration provides conversation history and vector search without installing a database server.

## Consequences
- Quick local demos and tutorials do not require additional infrastructure.
- Data is ephemeral; production setups should replace the memory configuration with a durable backend such as Postgres.
