# Entity Framework Submodule Guide

## Overview

The Entity Framework uses Git submodules to modularize plugin suites, reducing the core framework size by approximately 40% and allowing independent versioning of plugin collections.

## What are Git Submodules?

Git submodules are references to specific commits in external repositories. They allow you to include other Git repositories within your repository while maintaining their independence.

## Why Entity Uses Submodules

### Benefits
- **Reduced Core Size**: Core framework is ~40% smaller
- **Independent Versioning**: Each plugin suite can have its own release cycle
- **Optional Dependencies**: Users only install what they need
- **Cleaner Separation**: Clear boundaries between core and plugins
- **Parallel Development**: Teams can work on plugins independently

### Trade-offs
- **Additional Complexity**: Requires understanding of submodule commands
- **Extra Steps**: Cloning and updating requires additional commands
- **Version Coordination**: Need to manage compatibility between versions

## Plugin Repository Structure

Entity Framework plugins are organized into three main repositories:

1. **entity-plugin-examples**: Educational and demonstration plugins
2. **entity-plugin-stdlib**: Standard library of common utilities
3. **entity-plugin-gpt-oss**: GPT-OSS specific plugins

## Common Operations

### Cloning with Submodules

```bash
# Clone with all submodules
git clone --recursive https://github.com/Ladvien/entity.git

# Or if you already cloned without --recursive
git submodule update --init --recursive
```

### Updating Submodules

```bash
# Update all submodules to latest
git submodule update --remote

# Update specific submodule
git submodule update --remote entity-plugin-examples

# Pull latest changes in all submodules
git submodule foreach git pull origin main
```

### Making Changes to Submodules

```bash
# 1. Navigate to submodule directory
cd entity-plugin-examples

# 2. Create and checkout a new branch
git checkout -b feature/my-new-feature

# 3. Make your changes
edit src/entity_plugin_examples/my_plugin.py

# 4. Commit changes in submodule
git add .
git commit -m "feat: Add new plugin feature"

# 5. Push to submodule repository
git push origin feature/my-new-feature

# 6. Go back to main repository
cd ..

# 7. Update submodule reference
git add entity-plugin-examples
git commit -m "feat: Update entity-plugin-examples submodule"
```

### Handling Merge Conflicts

When merge conflicts occur in submodules:

```bash
# 1. Check submodule status
git submodule status

# 2. Enter the submodule
cd entity-plugin-examples

# 3. Resolve conflicts as normal
git status
git add <resolved-files>
git commit

# 4. Return to main repo and update reference
cd ..
git add entity-plugin-examples
git commit -m "fix: Resolve submodule conflicts"
```

## Developer Workflow

### Setting Up Development Environment

```bash
# 1. Clone the repository with submodules
git clone --recursive https://github.com/Ladvien/entity.git
cd entity

# 2. Install development dependencies
poetry install

# 3. Install submodule packages in development mode
cd entity-plugin-examples
poetry install
cd ..

cd entity-plugin-stdlib
poetry install
cd ..

cd entity-plugin-gpt-oss
poetry install
cd ..
```

### Making Changes Across Core and Plugins

```bash
# 1. Create feature branches in both repositories
git checkout -b feature/cross-repo-feature

cd entity-plugin-examples
git checkout -b feature/cross-repo-feature
cd ..

# 2. Make your changes in both places
# ... edit files ...

# 3. Commit in submodule first
cd entity-plugin-examples
git add .
git commit -m "feat: Plugin side of feature"
git push origin feature/cross-repo-feature
cd ..

# 4. Commit in main repository
git add .
git commit -m "feat: Core side of feature"
git push origin feature/cross-repo-feature
```

### Testing Changes Locally

```bash
# Run tests in main repository
poetry run pytest

# Run tests in each submodule
cd entity-plugin-examples
poetry run pytest
cd ..

cd entity-plugin-stdlib
poetry run pytest
cd ..

# Run integration tests
poetry run pytest tests/integration/
```

### Submitting PRs with Submodule Changes

1. **Create PR in submodule repository first**
   - Push your branch to the submodule repository
   - Create PR and get it reviewed
   - Merge the submodule PR

2. **Update main repository**
   - Update submodule to point to new commit
   - Create PR in main repository
   - Reference the submodule PR in description

## Troubleshooting

### Common Problems and Solutions

#### Detached HEAD in Submodule

```bash
cd entity-plugin-examples
git checkout main
git pull origin main
cd ..
git add entity-plugin-examples
git commit -m "fix: Update submodule to latest main"
```

#### Submodule Not Initialized

```bash
git submodule update --init --recursive
```

#### Wrong Submodule Commit

```bash
cd entity-plugin-examples
git checkout <correct-commit-hash>
cd ..
git add entity-plugin-examples
git commit -m "fix: Pin submodule to correct version"
```

#### Missing Submodule After Clone

```bash
git submodule update --init
```

#### Submodule Has Local Changes

```bash
cd entity-plugin-examples
git stash  # or commit changes
git checkout main
git pull origin main
```

### Recovery Procedures

#### Reset Submodule to Remote State

```bash
cd entity-plugin-examples
git reset --hard origin/main
cd ..
git submodule update --recursive
```

#### Complete Submodule Cleanup

```bash
# Remove submodule completely
git submodule deinit -f entity-plugin-examples
rm -rf .git/modules/entity-plugin-examples
git rm -f entity-plugin-examples

# Re-add submodule
git submodule add https://github.com/Ladvien/entity-plugin-examples
git submodule update --init --recursive
```

## Quick Reference

### Essential Commands

| Command | Description |
|---------|-------------|
| `git submodule status` | Show status of all submodules |
| `git submodule update --init` | Initialize submodules |
| `git submodule update --remote` | Update to latest remote commits |
| `git submodule foreach git pull` | Pull latest in all submodules |
| `git diff --submodule` | Show submodule changes |
| `git submodule sync` | Sync submodule URLs |

### Submodule-Specific Git Config

```bash
# Show submodule summary in git status
git config status.submoduleSummary true

# Show submodule changes in git diff
git config diff.submodule log

# Recurse into submodules by default
git config submodule.recurse true
```

## Migration Path

### For Existing Users

If you have existing code using the old import paths:

1. **Install new packages**:
   ```bash
   pip install entity-plugin-examples
   pip install entity-plugin-stdlib
   pip install entity-plugin-gpt-oss
   ```

2. **Update imports**:
   ```python
   # Old
   from entity.plugins.examples import CalculatorPlugin

   # New
   from entity_plugin_examples import CalculatorPlugin
   ```

3. **Run with deprecation warnings** to find remaining old imports:
   ```bash
   python -Wd your_script.py
   ```

### Deprecation Timeline

- **v0.1.x**: Compatibility layer available with deprecation warnings
- **v0.2.0**: Compatibility layer removed, must use new imports

## Support

For submodule-related issues:
- Check this guide first
- Search existing issues on GitHub
- Create a new issue with the `submodule` label
- Include output of `git submodule status` in bug reports
