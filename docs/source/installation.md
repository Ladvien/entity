# Installation Guide

## Requirements

Before installing Entity Framework, ensure you have:

- **Python 3.11 or higher** - Entity uses modern Python features
- **pip or Poetry** - For package management
- **Optional: Ollama** - For local LLM support
- **Optional: Docker** - For containerized deployments

## Quick Installation

### Using pip

```bash
# Install the latest stable version
pip install entity-core

# Or install with all optional dependencies
pip install "entity-core[all]"
```

### Using Poetry

```bash
# Add to your project
poetry add entity-core

# Or with optional dependencies
poetry add "entity-core[all]"
```

### Using uv (Ultra-fast)

```bash
# Install with uv
uv add entity-core
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

## Local LLM Setup (Recommended)

For local AI without cloud dependencies:

### Install Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model (3B parameter model, ~2GB)
ollama pull llama3.2:3b
```

### Verify Ollama

```bash
# Test Ollama is running
curl http://localhost:11434/api/tags

# Test with Entity
python -c "
from entity.defaults import load_defaults
resources = load_defaults()
print('✅ Ollama integration working!')
"
```

## Cloud LLM Setup (Alternative)

If you prefer cloud-based LLMs:

### OpenAI

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Anthropic Claude

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Google Gemini

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

## Development Installation

For contributing to Entity Framework:

### Clone and Install

```bash
# Clone the repository
git clone https://github.com/Ladvien/entity.git
cd entity

# Install with Poetry (recommended)
poetry install

# Or with pip in development mode
pip install -e .

# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
poetry run pre-commit install
```

### Run Tests

```bash
# Run test suite
poetry run pytest

# Run with coverage
poetry run pytest --cov=entity

# Run specific tests
poetry run pytest tests/test_workflow.py
```

## Docker Installation

For containerized deployments:

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Entity
RUN pip install entity-core

# Copy your agent configuration
COPY agent_config.yaml .

# Run your agent
CMD ["python", "-m", "entity.cli", "run", "agent_config.yaml"]
```

### Using Docker Compose

```yaml
version: '3.8'

services:
  entity-agent:
    image: python:3.11-slim
    volumes:
      - ./configs:/app/configs
    environment:
      - ENTITY_LOG_LEVEL=info
    command: |
      sh -c "
      pip install entity-core &&
      python -m entity.cli run /app/configs/agent.yaml
      "

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

## Platform-Specific Notes

### macOS

```bash
# If you encounter SSL certificate errors
pip install --upgrade certifi

# For Apple Silicon Macs
arch -arm64 pip install entity-core
```

### Windows

```bash
# Use Python from python.org, not Microsoft Store
# Run in PowerShell or Command Prompt as Administrator

# Install Entity
pip install entity-core

# For Ollama on Windows, use WSL2
wsl --install
# Then follow Linux instructions inside WSL2
```

### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3-pip

# Fedora/RHEL
sudo dnf install python3.11 python3-pip

# Install Entity
pip install entity-core
```

## Common Installation Issues

### Permission Errors

```bash
# Use --user flag
pip install --user entity-core

# Or use virtual environment (recommended)
python -m venv entity-env
source entity-env/bin/activate  # On Windows: entity-env\Scripts\activate
pip install entity-core
```

### Python Version Issues

```bash
# Check your Python version
python --version

# If needed, install Python 3.11+
# macOS with Homebrew
brew install python@3.11

# Or use pyenv for version management
curl https://pyenv.run | bash
pyenv install 3.11.7
pyenv global 3.11.7
```

### Dependency Conflicts

```bash
# Create isolated environment
python -m venv fresh-env
source fresh-env/bin/activate
pip install --upgrade pip
pip install entity-core

# Or use Poetry for better dependency management
poetry new my-agent-project
cd my-agent-project
poetry add entity-core
```

## Next Steps

Once installed successfully:

1. **Quick Start**: Follow our [5-Minute Tutorial](quickstart.md)
2. **Examples**: Explore the [Example Gallery](examples.md)
3. **Build Your Agent**: Check [Getting Started](getting_started.md)
4. **Learn Architecture**: Read about [Entity's Design](architecture.md)

## Getting Help

If you encounter issues:

- Check [GitHub Issues](https://github.com/Ladvien/entity/issues)
- Ask in [GitHub Discussions](https://github.com/Ladvien/entity/discussions)
- Review [Troubleshooting Guide](https://entity-core.readthedocs.io/troubleshooting)

Welcome to Entity Framework! 🚀
