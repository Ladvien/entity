# ADR 0003: Five-Minute Start Default

## Status
Accepted

## Context
Early experimentation should require no external services. A persistent database often slows first-time users, so the default memory plugin uses an in-process dictionary. DuckDB remains available for lightweight persistence.

## Decision
The default `memory` resource keeps data in memory only. New users can launch an agent with a single command, but history is lost on restart. The DuckDB example shows how to add simple persistence without running a server.

## Consequences
- Quick local demos and tutorials do not require additional infrastructure.
- Data is ephemeral; production setups should replace the memory configuration with a durable backend such as Postgres.
