# Changelog

All notable changes to the Entity Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive migration guide (MIGRATION.md) for GPT-OSS plugin modularization
- Optional dependencies support in pyproject.toml for modular plugin installation
- Integration tests for GPT-OSS plugin migration paths (test_gpt_oss_migration.py)
- Enhanced error messages in compatibility layer with detailed migration instructions
- Environment variable support (ENTITY_SUPPRESS_GPT_OSS_DEPRECATION) for CI/CD systems

### Changed
- **BREAKING**: GPT-OSS plugins moved to separate package `entity-plugin-gpt-oss`
  - Old import path `entity.plugins.gpt_oss` is deprecated
  - New import path `entity_plugin_gpt_oss` should be used
  - Compatibility layer provides backward compatibility until v0.1.0
- Updated README.md with plugin packages section and migration notice
- Enhanced gpt_oss_compat.py with version checking and logging capabilities
- Improved documentation structure with clear modularization explanation

### Deprecated
- Import path `entity.plugins.gpt_oss` - will be removed in v0.1.0 (Q2 2024)
  - Affects all 9 GPT-OSS plugins:
    - ReasoningTracePlugin
    - StructuredOutputPlugin
    - DeveloperOverridePlugin
    - AdaptiveReasoningPlugin
    - GPTOSSToolOrchestrator
    - MultiChannelAggregatorPlugin
    - HarmonySafetyFilterPlugin
    - FunctionSchemaRegistryPlugin
    - ReasoningAnalyticsDashboardPlugin

### Removed
- 9 duplicate GPT-OSS plugin implementation files (~243KB of code)
  - Moved to entity-plugin-gpt-oss package
  - Replaced with compatibility shims

## [0.0.12] - Previous Release

### Added
- Initial Entity Framework release with monolithic plugin structure
- Built-in GPT-OSS plugins in core package
- Basic plugin architecture and workflow stages
- Memory system and resource management
- YAML-based configuration support

### Known Issues
- Code duplication between core and plugin packages (resolved in upcoming release)
- Large core package size due to bundled plugins (resolved via modularization)

## Migration Instructions

To migrate to the new modular structure:

1. Install the GPT-OSS plugin package:
   ```bash
   pip install entity-plugin-gpt-oss
   ```

2. Update your imports:
   ```python
   # Old (deprecated)
   from entity.plugins.gpt_oss import ReasoningTracePlugin

   # New (recommended)
   from entity_plugin_gpt_oss import ReasoningTracePlugin
   ```

3. See [MIGRATION.md](MIGRATION.md) for detailed migration guide

## Compatibility

- The compatibility layer ensures existing code continues to work with deprecation warnings
- Full removal of legacy import paths scheduled for v0.1.0 (Q2 2024)
- Environment variable `ENTITY_SUPPRESS_GPT_OSS_DEPRECATION=1` can suppress warnings

## Links

- [Migration Guide](MIGRATION.md)
- [GitHub Repository](https://github.com/Ladvien/entity)
- [Documentation](https://entity-core.readthedocs.io)
- [PyPI Package](https://pypi.org/project/entity-core/)

---

For more details on each change, please refer to the commit history and pull requests on GitHub.
