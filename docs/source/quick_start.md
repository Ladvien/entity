# Quick Start

Follow these steps to get a basic agent running.

## 1. Install

Install the framework with pip or add it to your Poetry project:

```bash
pip install entity
# or
poetry add entity
```

## 2. Scaffold a project

Create a starter layout using the built-in generator:

```bash
entity-cli new my_agent
cd my_agent
```

This command creates `config/dev.yaml` and `src/main.py`.

## 3. Run the sample agent

Start the HTTP server and send a message:

```bash
poetry run python src/main.py
curl -X POST -H "Content-Type: application/json" \
     -d '{"message": "hello"}' http://localhost:8000/
```

You should see a simple reply from the example pipeline.

## Troubleshooting

- Activate your virtual environment if `entity-cli` is not found.
- Missing packages? Run `poetry install --with dev` in the project root.
- Use `--debug` with any command for verbose logs.

## What's next?

Head over to the [Plugin Development Guide](plugin_guide.md) to extend the agent with custom logic.
