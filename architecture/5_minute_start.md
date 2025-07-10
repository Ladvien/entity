# 5-Minute Start

The framework aims to get developers experimenting in minutes. The default `Memory` resource automatically configures DuckDB in memory so no database setup is required. This choice trades durability for speed during early exploration. Because DuckDB runs in the same process, the agent can start, store conversation history, and run tools without external dependencies.

For production deployments you can switch to Postgres or any other supported backend by updating the `memory` configuration in your YAML file. The in-memory DuckDB setup is kept small so new users can try the agent with a single command.
