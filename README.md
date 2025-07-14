# Entity Pipeline Framework

[![Build Status](https://github.com/Ladvien/entity/actions/workflows/test.yml/badge.svg)](https://github.com/Ladvien/entity/actions/workflows/test.yml)
[![Docs](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://entity.readthedocs.io/en/latest/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Plugin Tool

Generate a new prompt plugin:

```bash
plugin-tool generate my_prompt --type prompt
```

Run the plugin in isolation:

```bash
plugin-tool test src/my_prompt.py
```

Create Markdown docs from the plugin docstring:

```bash
plugin-tool docs src/my_prompt.py --out docs
```

## Default Workflow

`Layer0SetupManager` creates local resources and ships with a ready-made
`default_workflow`. The global `agent` picks up this workflow automatically,
so no extra configuration is required.

```python
import asyncio
from entity import agent
from entity.utils.setup_manager import Layer0SetupManager
from entity.workflows import default_workflow

# uses `default_workflow` when none is provided
asyncio.run(Layer0SetupManager().setup())
print(asyncio.run(agent.handle("Hello")))
```

## Example Plugins

Check the `src/plugins/examples` directory for minimal plugins demonstrating the
INPUT, PARSE, and REVIEW stages. Each shows how to interact with the
`PluginContext` during execution. These plugins are registered in the
`DefaultWorkflow` for quick experimentation. The rendered source is available in the
[Plugin Examples](https://entity.readthedocs.io/en/latest/plugin_examples.html)
documentation.

## Running Tests

Before running the test suite, install the development extras. Without these
dependencies the `entity` package fails to import and tests will crash.

```bash
poetry install --with dev
# or
pip install -e ".[dev]"
```

With dependencies installed you can run the included poe tasks:

```bash
poe test
```

For more detailed output use the verbose task:

```bash
poe test-verbose
```

## Multi-User Support

Pass a unique `user_id` when calling `agent.chat()` or `agent.handle()` to keep
conversation history and memory isolated per user.

```python
response = await agent.chat("Hi", user_id="alice")
```

See [multi_user](docs/source/multi_user.md) for additional patterns.

