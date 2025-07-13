# Configuration

Entity uses a single YAML file to configure plugins and resources. Environment variables can be interpolated using the standard `.env` file.

## Overlay Files

Pass `--env <name>` to `entity-cli` to merge `config/<name>.yaml` over the base configuration. Only keys present in the overlay override values from the primary file.

```bash
poetry run entity-cli --config config/dev.yaml --env prod run
```

This command loads `config/dev.yaml` and then applies the settings from `config/prod.yaml` before starting the agent.

## Generating JSON Schema

Run `python docs/generate_config_docs.py` to create `config_schema.json` describing all configuration models.

## Migrating Legacy Configs

Use :class:`entity.config.ConfigMigrator` to rename fields in older YAML files.
```python
from entity.config import ConfigMigrator

migrator = ConfigMigrator({"old_name": "new_name"})
migrator.migrate_file("config/dev.yaml")
```
