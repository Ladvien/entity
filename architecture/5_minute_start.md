# 5-Minute Start

The framework aims to get developers experimenting in minutes. The default `Memory` resource stores data only in memory so no database setup is required. This choice trades durability for speed during early exploration. Use a custom resource such as DuckDB when you need to persist history.

For production deployments you can switch to Postgres or any other supported backend by updating the `memory` configuration in your YAML file. The ephemeral setup keeps the quick start simple, but you will want a persistent backend before moving to production.
