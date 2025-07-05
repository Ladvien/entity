# Project Setup

Follow these steps to install dependencies and scaffold a new project.

1. Install Python 3.11+ and [Poetry](https://python-poetry.org/).
2. Run `poetry install` to create the virtual environment. This installs
   all dependencies, including the required `httpx==0.27.*`.
3. Copy `.env.example` to `.env` and provide any required credentials.
4. Generate a starter project:

```bash
python -m src.cli -c config/template.yaml new my_agent
```

This creates `my_agent/config/dev.yaml` and `my_agent/src/main.py`.
