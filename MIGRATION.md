# GPT-OSS Plugin Migration Guide

## Overview

The Entity Framework has modularized the GPT-OSS plugin suite into a separate package (`entity-plugin-gpt-oss`) to improve maintainability, reduce core framework size, and allow independent versioning. This guide will help you migrate from the legacy import paths to the new modular structure.

## Timeline

- **Current**: Compatibility layer provides backward compatibility with deprecation warnings
- **v0.1.0 (Q2 2024)**: Legacy import paths will be removed
- **Recommended**: Migrate to new import paths as soon as possible

## Quick Migration Steps

### 1. Install the New Package

```bash
# Using pip
pip install entity-plugin-gpt-oss

# Using poetry
poetry add entity-plugin-gpt-oss

# Using uv
uv add entity-plugin-gpt-oss

# Or as an optional dependency with entity-core
pip install "entity-core[gpt-oss]"
```

### 2. Update Your Imports

#### Old Way (Deprecated)
```python
from entity.plugins.gpt_oss import ReasoningTracePlugin
from entity.plugins.gpt_oss import StructuredOutputPlugin
from entity.plugins.gpt_oss import DeveloperOverridePlugin
```

#### New Way (Recommended)
```python
from entity_plugin_gpt_oss import ReasoningTracePlugin
from entity_plugin_gpt_oss import StructuredOutputPlugin
from entity_plugin_gpt_oss import DeveloperOverridePlugin
```

### 3. Update Configuration Files

If you reference GPT-OSS plugins in YAML configuration files, ensure the new package is installed but keep the same plugin names:

```yaml
# No changes needed in YAML - plugin names remain the same
plugins:
  - name: ReasoningTracePlugin
    enabled: true
  - name: StructuredOutputPlugin
    enabled: true
```

## Complete Plugin List

All nine GPT-OSS plugins have been moved to the new package:

| Plugin Name | Old Import | New Import |
|------------|------------|------------|
| ReasoningTracePlugin | `entity.plugins.gpt_oss` | `entity_plugin_gpt_oss` |
| StructuredOutputPlugin | `entity.plugins.gpt_oss` | `entity_plugin_gpt_oss` |
| DeveloperOverridePlugin | `entity.plugins.gpt_oss` | `entity_plugin_gpt_oss` |
| AdaptiveReasoningPlugin | `entity.plugins.gpt_oss` | `entity_plugin_gpt_oss` |
| GPTOSSToolOrchestrator | `entity.plugins.gpt_oss` | `entity_plugin_gpt_oss` |
| MultiChannelAggregatorPlugin | `entity.plugins.gpt_oss` | `entity_plugin_gpt_oss` |
| HarmonySafetyFilterPlugin | `entity.plugins.gpt_oss` | `entity_plugin_gpt_oss` |
| FunctionSchemaRegistryPlugin | `entity.plugins.gpt_oss` | `entity_plugin_gpt_oss` |
| ReasoningAnalyticsDashboardPlugin | `entity.plugins.gpt_oss` | `entity_plugin_gpt_oss` |

## Helper Classes and Enums

Helper classes and enums are also available from the new package:

```python
# Old way (deprecated)
from entity.plugins.gpt_oss import ReasoningLevel, ReasoningTrace
from entity.plugins.gpt_oss import OutputFormat, ValidationResult

# New way (recommended)
from entity_plugin_gpt_oss import ReasoningLevel, ReasoningTrace
from entity_plugin_gpt_oss import OutputFormat, ValidationResult
```

## Handling Deprecation Warnings

### Suppressing Warnings in CI/CD

For CI/CD pipelines that need time to migrate, you can temporarily suppress deprecation warnings:

```bash
# Set environment variable
export ENTITY_SUPPRESS_GPT_OSS_DEPRECATION=1

# Or in Python
import os
os.environ['ENTITY_SUPPRESS_GPT_OSS_DEPRECATION'] = '1'
```

### Finding Deprecated Imports

Use grep to find all occurrences of old imports in your codebase:

```bash
# Find all old imports
grep -r "from entity.plugins.gpt_oss" .
grep -r "import entity.plugins.gpt_oss" .
```

## Troubleshooting

### Import Error: Module Not Found

**Problem**: `ModuleNotFoundError: No module named 'entity_plugin_gpt_oss'`

**Solution**: Install the package:
```bash
pip install entity-plugin-gpt-oss
```

### Import Error: Plugin Not Available

**Problem**: `ImportError: GPT-OSS Plugin Not Available`

**Solution**: The compatibility layer is working but the new package isn't installed. Install it:
```bash
pip install entity-plugin-gpt-oss
```

### Version Incompatibility

**Problem**: Plugin features not working as expected after migration

**Solution**: Ensure you have compatible versions:
```bash
pip install --upgrade entity-core entity-plugin-gpt-oss
```

### Circular Import Issues

**Problem**: Circular import errors after migration

**Solution**: Check that you're not mixing old and new import styles. Use one consistently:
```python
# Don't mix these in the same file
from entity.plugins.gpt_oss import ReasoningTracePlugin  # Old
from entity_plugin_gpt_oss import StructuredOutputPlugin  # New

# Use one style consistently
from entity_plugin_gpt_oss import ReasoningTracePlugin, StructuredOutputPlugin  # Recommended
```

## Benefits of Modularization

### For Users
- **Smaller Core**: Reduced entity-core package size by ~40%
- **Optional Installation**: Only install plugins you need
- **Faster Installation**: Smaller downloads and dependency resolution
- **Independent Updates**: Plugin updates don't require core framework updates

### For Developers
- **Better Maintainability**: Isolated plugin development and testing
- **Clearer Dependencies**: Plugin-specific dependencies don't affect core
- **Faster CI/CD**: Smaller test suites and build times
- **Easier Contribution**: Focus on specific plugin functionality

## Migration Checklist

- [ ] Install `entity-plugin-gpt-oss` package
- [ ] Update all import statements from old to new paths
- [ ] Run tests to ensure functionality is preserved
- [ ] Update any documentation or README files
- [ ] Update CI/CD configurations to install the new package
- [ ] Remove temporary deprecation warning suppressions after migration
- [ ] Update `requirements.txt` or `pyproject.toml` dependencies

## Getting Help

If you encounter issues during migration:

1. Check this guide for common problems and solutions
2. Review the [compatibility layer source code](src/entity/plugins/gpt_oss_compat.py)
3. Open an issue on [GitHub](https://github.com/Ladvien/entity/issues)
4. Join our [Discord community](https://discord.gg/entity-framework) for support

## Example Migration

### Before (Legacy Code)
```python
# old_agent.py
from entity import Agent
from entity.plugins.gpt_oss import (
    ReasoningTracePlugin,
    StructuredOutputPlugin,
    AdaptiveReasoningPlugin
)

agent = Agent(
    plugins=[
        ReasoningTracePlugin(),
        StructuredOutputPlugin(),
        AdaptiveReasoningPlugin()
    ]
)
```

### After (Migrated Code)
```python
# new_agent.py
from entity import Agent
from entity_plugin_gpt_oss import (
    ReasoningTracePlugin,
    StructuredOutputPlugin,
    AdaptiveReasoningPlugin
)

agent = Agent(
    plugins=[
        ReasoningTracePlugin(),
        StructuredOutputPlugin(),
        AdaptiveReasoningPlugin()
    ]
)
```

### Package Dependencies Update

#### Before (pyproject.toml)
```toml
[tool.poetry.dependencies]
entity-core = "^0.0.12"
# GPT-OSS plugins were included in entity-core
```

#### After (pyproject.toml)
```toml
[tool.poetry.dependencies]
entity-core = "^0.0.12"
entity-plugin-gpt-oss = "^0.1.0"  # Add this line
```

## Notes for Package Maintainers

If you maintain a package that depends on Entity Framework with GPT-OSS plugins:

1. Add `entity-plugin-gpt-oss` to your dependencies
2. Update your documentation to reflect the new import paths
3. Consider making it an optional dependency if not all users need GPT-OSS plugins
4. Test with both old (with compatibility layer) and new import paths during transition

## Additional Resources

For more information about this release:

- **[Release Notes](RELEASE_NOTES.md)**: Complete details about v0.1.0 changes and improvements
- **[Performance Benchmarks](benchmarks/import_performance_report.md)**: Detailed performance analysis
- **[Compatibility Timeline](COMPATIBILITY_TIMELINE.md)**: Support schedule and migration timeline

---

*Last updated: Q2 2024*
*Entity Framework Version: 0.1.0*
*Target Removal Version: 0.2.0*
