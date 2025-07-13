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

