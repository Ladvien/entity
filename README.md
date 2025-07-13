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

`Layer0SetupManager` creates basic resources and provides `DefaultWorkflow`.
The global `agent` uses this workflow automatically.

```python
import asyncio
from entity import agent
from entity.utils.setup_manager import Layer0SetupManager

asyncio.run(Layer0SetupManager().setup())
print(asyncio.run(agent.handle("Hello")))
```

## Example Plugins

Check the `examples/plugins` directory for minimal plugins demonstrating the
INPUT, PARSE, and REVIEW stages. Each shows how to interact with the
`PluginContext` during execution. The rendered source is available in the
[Plugin Examples](https://entity.readthedocs.io/en/latest/plugin_examples.html)
documentation.

