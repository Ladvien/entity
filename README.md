# Entity Pipeline Framework

[![Build Status](https://github.com/Ladvien/entity/actions/workflows/test.yml/badge.svg)](https://github.com/Ladvien/entity/actions/workflows/test.yml)
[![Docs](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://entity.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Entity lets you craft agent pipelines using a single configuration file. The same YAML works locally and in production, so iteration stays simple. By default the agent stores conversation data in an in-memory DuckDB database so you can try things instantly.

## Key Features
- Three-layer plugin system for progressive complexity
- Hot-reloadable YAML config with validation
- Stateless workers that scale horizontally
- Unified memory resource for chat, search, and storage
- In-memory DuckDB backend for quick local testing

Check the [hero landing page](https://entity.readthedocs.io/en/latest/) for a visual overview.

## Minimal Example
```bash
poetry run entity-cli --config config/dev.yaml
```

See the [Quick Start](docs/source/quick_start.md) for step-by-step setup or browse the [full documentation](https://entity.readthedocs.io/en/latest/). For plugin inspection see the [Analyze Plugin Functions](docs/source/plugin_guide.md#analyze-plugin-functions) section.
