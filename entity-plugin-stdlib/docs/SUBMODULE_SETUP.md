# Entity Plugin Submodule Setup Guide

## Overview

This guide explains how to set up and manage Entity Framework plugins as Git submodules. Using submodules allows you to maintain separate repositories for plugins while integrating them seamlessly into the main Entity Framework.

## Prerequisites

- Git 2.13 or later
- Entity Framework Core installed
- Python 3.8+ environment
- Poetry (for dependency management)

## Adding a Plugin as a Submodule

### 1. From the Entity Framework Root Directory

```bash
# Navigate to your entity-core root directory
cd /path/to/entity-core

# Add the plugin as a submodule
git submodule add https://github.com/yourusername/entity-plugin-[name].git plugins/[name]

# Initialize and update the submodule
git submodule update --init --recursive

# Commit the submodule addition
git add .gitmodules plugins/[name]
git commit -m "Add [name] plugin as submodule"
```

### 2. Verify Installation

```bash
# Check submodule status
git submodule status

# Verify the plugin directory exists
ls -la plugins/[name]

# Test import (from entity-core root)
python -c "import sys; sys.path.insert(0, 'plugins/[name]/src'); import entity_plugin_[name]"
```

## Cloning a Repository with Submodules

When cloning the Entity Framework repository that contains submodules:

```bash
# Clone with submodules included
git clone --recursive https://github.com/Ladvien/entity.git

# Or if already cloned without --recursive
git submodule update --init --recursive
```

## Updating Submodules

### Update to Latest Commit

```bash
# Update all submodules to their latest commits
git submodule update --remote --merge

# Update a specific plugin
git submodule update --remote --merge plugins/[name]

# Commit the updates
git add plugins/[name]
git commit -m "Update [name] plugin to latest version"
```

### Update to Specific Version

```bash
# Navigate to the submodule directory
cd plugins/[name]

# Checkout specific tag or commit
git checkout v1.2.3

# Return to main repository
cd ../..

# Commit the version change
git add plugins/[name]
git commit -m "Pin [name] plugin to v1.2.3"
```

## Working with Submodules

### Making Changes to a Plugin

```bash
# Navigate to the plugin directory
cd plugins/[name]

# Create a feature branch
git checkout -b feature/my-feature

# Make your changes
# ... edit files ...

# Commit changes in the submodule
git add .
git commit -m "Add new feature"

# Push to the plugin repository
git push origin feature/my-feature

# Return to main repository
cd ../..

# Update the main repository to track the new commit
git add plugins/[name]
git commit -m "Update [name] plugin with new feature"
```

### Developing Locally

For local development without pushing changes:

```bash
# Navigate to plugin directory
cd plugins/[name]

# Make changes and test locally
poetry install -e .
poetry run pytest

# Changes are only local until you commit and push
```

## Configuration

### .gitmodules File

The `.gitmodules` file tracks all submodules:

```ini
[submodule "plugins/[name]"]
    path = plugins/[name]
    url = https://github.com/yourusername/entity-plugin-[name].git
    branch = main
```

### Submodule Configuration Options

```bash
# Configure submodule to track a specific branch
git config -f .gitmodules submodule.plugins/[name].branch develop

# Enable recursive updates
git config submodule.recurse true

# Set update strategy
git config submodule.plugins/[name].update merge
```

## Integration with Entity Framework

### Automatic Plugin Discovery

Entity Framework automatically discovers plugins in the `plugins/` directory:

```python
# entity/core/plugin_loader.py
import os
import importlib.util
from pathlib import Path

def load_plugins():
    """Automatically load all plugins from the plugins directory."""
    plugins_dir = Path(__file__).parent.parent.parent / "plugins"

    for plugin_path in plugins_dir.iterdir():
        if plugin_path.is_dir() and (plugin_path / "src").exists():
            # Add plugin to Python path
            sys.path.insert(0, str(plugin_path / "src"))

            # Import the plugin module
            module_name = f"entity_plugin_{plugin_path.name}"
            try:
                plugin = importlib.import_module(module_name)
                register_plugin(plugin)
            except ImportError as e:
                print(f"Failed to load plugin {plugin_path.name}: {e}")
```

### Manual Plugin Loading

For more control over plugin loading:

```python
from entity.workflow.executor import WorkflowExecutor
import sys

# Add plugin to path
sys.path.insert(0, "plugins/[name]/src")

# Import and use plugin
from entity_plugin_[name] import MyPlugin

executor = WorkflowExecutor()
plugin = MyPlugin(config={...})
executor.add_plugin(plugin)
```

## CI/CD Integration

### GitHub Actions Workflow

Add submodule support to your CI/CD pipeline:

```yaml
name: Test with Plugins

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout with submodules
      uses: actions/checkout@v3
      with:
        submodules: recursive
        token: ${{ secrets.GITHUB_TOKEN }}

    - name: Update submodules
      run: git submodule update --init --recursive

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install poetry
        poetry install

        # Install plugin dependencies
        for plugin in plugins/*; do
          if [ -f "$plugin/pyproject.toml" ]; then
            cd "$plugin"
            poetry install
            cd -
          fi
        done

    - name: Run tests
      run: |
        poetry run pytest

        # Test plugins
        for plugin in plugins/*; do
          if [ -d "$plugin/tests" ]; then
            cd "$plugin"
            poetry run pytest
            cd -
          fi
        done
```

## Best Practices

### 1. Version Management

- **Tag releases** in plugin repositories
- **Pin specific versions** in production
- **Use branch tracking** for development

### 2. Dependency Management

- Keep plugin dependencies isolated
- Use Poetry for consistent environments
- Document dependency conflicts

### 3. Testing

- Test plugins independently
- Run integration tests with main framework
- Maintain CI/CD for both plugin and main repos

### 4. Documentation

- Document plugin-specific setup requirements
- Maintain compatibility matrix
- Provide migration guides for breaking changes

## Troubleshooting

### Common Issues

#### Submodule Not Initialized

```bash
# Error: No submodule mapping found
git submodule init
git submodule update
```

#### Authentication Issues

```bash
# Use SSH instead of HTTPS
git config submodule.plugins/[name].url git@github.com:yourusername/entity-plugin-[name].git
```

#### Detached HEAD State

```bash
cd plugins/[name]
git checkout main
git pull origin main
cd ../..
git add plugins/[name]
git commit -m "Update plugin to latest main"
```

#### Missing Submodule Content

```bash
# Force update
git submodule update --init --recursive --force

# Or remove and re-add
git submodule deinit -f plugins/[name]
git rm -f plugins/[name]
rm -rf .git/modules/plugins/[name]
git submodule add https://github.com/yourusername/entity-plugin-[name].git plugins/[name]
```

## Advanced Usage

### Sparse Checkout

For large plugins, use sparse checkout:

```bash
cd plugins/[name]
git sparse-checkout init --cone
git sparse-checkout set src tests
```

### Submodule Foreach

Execute commands in all submodules:

```bash
# Update all plugins
git submodule foreach 'git pull origin main'

# Run tests in all plugins
git submodule foreach 'poetry run pytest'

# Check status of all plugins
git submodule foreach 'git status'
```

### Custom Update Scripts

Create a script for complex update workflows:

```bash
#!/bin/bash
# update-plugins.sh

echo "Updating Entity Framework plugins..."

# Update each plugin
for plugin in plugins/*; do
    if [ -d "$plugin/.git" ]; then
        echo "Updating $(basename $plugin)..."
        cd "$plugin"
        git fetch
        git checkout main
        git pull origin main
        poetry install
        poetry run pytest
        cd - > /dev/null
    fi
done

echo "All plugins updated successfully!"
```

## Security Considerations

### Submodule Security

1. **Verify repository URLs** before adding submodules
2. **Use SSH keys** for private repositories
3. **Review code** before updating submodules
4. **Pin versions** in production environments
5. **Audit dependencies** regularly

### Access Control

```bash
# Use deploy keys for read-only access
git config submodule.plugins/[name].url git@github.com:yourusername/entity-plugin-[name].git

# Configure credential helper
git config credential.helper store
```

## Migration Guide

### Converting Existing Plugin to Submodule

1. **Export plugin history**:
```bash
cd existing-plugin
git filter-branch --prune-empty --subdirectory-filter src HEAD
```

2. **Create new repository**:
```bash
git init entity-plugin-[name]
cd entity-plugin-[name]
git remote add origin https://github.com/yourusername/entity-plugin-[name].git
```

3. **Import history**:
```bash
git pull /path/to/filtered/repo main
```

4. **Add as submodule**:
```bash
cd /path/to/entity-core
git submodule add https://github.com/yourusername/entity-plugin-[name].git plugins/[name]
```

## Resources

- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Entity Framework Documentation](https://entity-core.readthedocs.io)
- [Plugin Development Guide](../README.md)
- [Entity Framework Repository](https://github.com/Ladvien/entity)

## Support

For issues or questions:
- Open an issue in the plugin repository
- Contact the Entity Framework team
- Check the [FAQ](https://entity-core.readthedocs.io/faq)
