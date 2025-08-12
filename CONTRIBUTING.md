# Contributing to Entity

First off, thank you for considering contributing to Entity! It's people like you that make Entity such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our principles of respectful and constructive collaboration.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include logs and error messages if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the style guidelines
6. Issue that pull request!

## Development Setup

### Prerequisites

* Python 3.11 or higher
* Poetry for dependency management
* Docker (optional, for integration tests)
* GitHub CLI (`gh`) for plugin development

### Setting Up Your Development Environment

1. Clone your fork with submodules:
```bash
# Replace YOUR_USERNAME with your GitHub username
git clone --recurse-submodules https://github.com/YOUR_USERNAME/entity.git
cd entity

# Or if you already cloned without submodules
git submodule init
git submodule update
```

2. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install dependencies:
```bash
poetry install --with dev
```

4. Activate the virtual environment:
```bash
poetry shell
```

### Running Tests

Run the full test suite:
```bash
poetry run poe test
```

Run tests with coverage:
```bash
poetry run poe test-coverage
```

Run specific test categories:
```bash
poetry run poe test-architecture  # Architecture tests
poetry run poe test-plugins       # Plugin tests
poetry run poe test-resources     # Resource tests
```

Run integration tests with Docker:
```bash
poetry run poe test-with-docker
```

### Code Style

We use Black for code formatting and follow PEP 8 guidelines. Before submitting:

1. Format your code:
```bash
poetry run black src tests
```

2. Run linting:
```bash
poetry run flake8 src tests
```

3. Run the full quality check:
```bash
poetry run poe check
```

### Documentation

We use Google-style docstrings. Every public class and function should have:

* A brief description
* Args section documenting parameters
* Returns section documenting return values
* Raises section documenting exceptions
* Examples section when appropriate

Example:
```python
def process_message(message: str, user_id: str = "default") -> str:
    """Process a message through the agent workflow.

    Args:
        message: The input message to process.
        user_id: Unique identifier for the user. Defaults to "default".

    Returns:
        The processed response from the agent.

    Raises:
        ValueError: If message is empty.

    Examples:
        >>> response = process_message("Hello!")
        >>> print(response)
        "Hi there!"
    """
```

Build documentation locally:
```bash
poetry run sphinx-build -b html docs/source docs/build
```

### Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Architecture Guidelines

Please follow the 4-layer architecture:

1. **Layer 1: Infrastructure** - Concrete technology implementations
2. **Layer 2: Resources** - Technology-agnostic resource interfaces
3. **Layer 3: Canonical Resources** - Core building blocks (Memory, LLM, FileStorage, Logging)
4. **Layer 4: Agent** - Composition of resources with workflow

### Plugin Development

#### Contributing to Existing Plugins

If you want to contribute to an existing plugin (examples, gpt-oss, stdlib, template):

1. Fork the plugin repository using GitHub CLI:
```bash
# Fork a plugin repository
gh repo fork Ladvien/entity-plugin-examples --clone

# Or fork and create a PR branch
gh repo fork Ladvien/entity-plugin-gpt-oss --clone
cd entity-plugin-gpt-oss
git checkout -b feature/my-improvement
```

2. Make your changes and test locally:
```bash
# In the plugin directory
poetry install --with dev
poetry run pytest

# Test with the main entity framework
cd ../entity
git submodule update --remote plugins/examples  # Update to your fork
poetry run pytest tests/plugins/
```

3. Submit a pull request:
```bash
# From your plugin directory
gh pr create --title "Add new feature" --body "Description of changes"
```

#### Creating New Plugins

When creating new plugins:

1. Inherit from the appropriate base class (`PromptPlugin`, `ToolPlugin`, etc.)
2. Declare supported stages in `supported_stages`
3. Implement `validate_config()` and `validate_workflow()` methods
4. Implement `_execute_impl()` for the plugin logic
5. Add comprehensive tests

Example:
```python
class MyPlugin(PromptPlugin):
    supported_stages = [THINK, REVIEW]
    dependencies = ["llm", "memory"]

    def validate_config(self) -> ValidationResult:
        # Validate configuration
        return ValidationResult.success()

    async def _execute_impl(self, context: PluginContext) -> None:
        # Plugin implementation
        result = await self.call_llm(context, "Process this...")
        await context.remember("result", result.content)
```

#### Plugin Repository Structure

Each plugin should follow this structure:
```
entity-plugin-yourname/
├── src/
│   └── entity_plugin_yourname/
│       ├── __init__.py
│       └── your_plugin.py
├── tests/
│   └── test_your_plugin.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## Testing Guidelines

* Write tests for all new functionality
* Maintain at least 80% code coverage
* Use pytest fixtures for reusable test data
* Mock external dependencies appropriately
* Include both unit and integration tests

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a pull request with the version bump
4. After merge, create a GitHub release
5. The CI/CD pipeline will automatically publish to PyPI

## Security Considerations

### Using Personal Access Tokens (PATs)

When working with plugin repositories, especially private ones, you'll need to use Personal Access Tokens:

1. **Create a fine-grained PAT on GitHub:**
   - Go to Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Click "Generate new token"
   - Select only the repositories you need
   - Grant minimal permissions:
     - Contents: Read (for cloning)
     - Contents: Write (for pushing changes)
     - Pull requests: Write (for creating PRs)
   - Set a reasonable expiration date

2. **Use the PAT securely:**
```bash
# Authenticate GitHub CLI with your PAT
gh auth login

# Or configure git to use the PAT
git config --global credential.helper store
```

3. **Security best practices:**
   - **Never commit PATs** to any repository
   - Store PATs in a secure password manager
   - Use environment variables in CI/CD: `export GITHUB_TOKEN=your_pat`
   - Rotate tokens regularly (every 90 days recommended)
   - Use repository-specific tokens when possible
   - Revoke tokens immediately if compromised

### Handling Sensitive Data

- Never include API keys, passwords, or secrets in code
- Use `.env` files for local development (and add to `.gitignore`)
- Review your changes for accidental credential exposure before committing
- Use `git-secrets` or similar tools to prevent secret commits

## Questions?

Feel free to open an issue for any questions about contributing!
