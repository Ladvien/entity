# Installation Guide

## Requirements

```{include} ../../README.md
:start-after: ## 📋 Requirements
:end-before: ## 🚀 Installation
```

## Installation

```{include} ../../README.md
:start-after: ## 🚀 Installation
:end-before: ## 📚 Documentation & Examples
```

## Verify Installation

After installation, verify Entity Framework is working:

```bash
# Test basic installation
python -c "import entity; print('Entity Framework installed successfully!')"

# Run a quick test agent
python -c "
from entity import Agent
from entity.defaults import load_defaults
import asyncio

async def test():
    resources = load_defaults()
    agent = Agent(resources=resources)
    print('✅ Entity agent created successfully!')

asyncio.run(test())
"
```

## Development Installation

If you want to contribute to Entity Framework or run from source:

```bash
# Clone the repository
git clone https://github.com/Ladvien/entity.git
cd entity

# Install with Poetry (recommended)
poetry install

# Or with pip in development mode
pip install -e .

# Install development dependencies
poetry install --dev

# Run tests to verify everything works
poetry run pytest
```

## Common Installation Issues

### Permission Errors
If you encounter permission errors:
```bash
# Use --user flag
pip install --user entity-core

# Or use virtual environment (recommended)
python -m venv entity-env
source entity-env/bin/activate  # On Windows: entity-env\Scripts\activate
pip install entity-core
```

### Python Version Issues
Entity requires Python 3.11 or higher:
```bash
# Check your Python version
python --version

# If needed, install Python 3.11+ from python.org
# Or use pyenv to manage multiple Python versions
```

### LLM Setup
For local LLM support with Ollama:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a small model for testing
ollama pull llama3.2:3b

# Start Ollama server
ollama serve
```

## Next Steps

Once installed, check out our [Getting Started Guide](getting_started.md) or jump straight into the [5-Minute Quick Start Tutorial](quickstart.md)!
