# Secrets and Environment Variables

Configuration files may reference environment variables using the `${VAR}` syntax. Call `load_env()` before loading your YAML or JSON to populate these values.

`load_env()` reads variables from two places:

1. The project `.env` file.
2. `secrets/<env>.env` where `<env>` matches the environment name, such as `dev` or `prod`.

Existing process variables are never overwritten. Values from the secrets file override those from `.env` when both define the same key.

Store API keys and other credentials in the `secrets/` directory and keep these files out of version control.

## Local Setup Helper

``Layer0SetupManager`` prepares a working environment by creating the default
`agent_memory.duckdb` database and the `agent_files/` directory. It verifies that
Ollama is running and downloads the configured model when needed.

```python
from entity.utils.setup_manager import Layer0SetupManager
import asyncio

asyncio.run(Layer0SetupManager().setup())
```

If dependencies like DuckDB are missing the helper prints clear instructions
instead of raising errors.
