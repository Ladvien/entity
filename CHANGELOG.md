# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.2] - 2024-08-08

### Added
- Comprehensive Sphinx documentation infrastructure
- API documentation with autodoc support
- Complete package metadata for PyPI publishing
- Google-style docstrings for core modules
- CHANGELOG.md following Keep a Changelog format
- CONTRIBUTING.md with development guidelines
- ReadTheDocs integration
- Automated PyPI publishing via Poetry/Poe tasks

### Changed
- Enhanced package description and keywords for better discoverability
- Improved Agent class documentation with usage examples
- Package renamed to entity-core for PyPI

### Fixed
- Documentation build configuration for ReadTheDocs

## [0.0.1] - 2024-01-01

### Added
- Initial release of Entity framework
- Core Agent class with zero-config defaults
- 4-Layer resource system architecture
- 6-Stage workflow (INPUT → PARSE → THINK → DO → REVIEW → OUTPUT)
- Canonical resources: Memory, LLM, FileStorage, Logging
- Plugin-based architecture for extensibility
- Built-in workflow templates
- Support for vLLM and Ollama as LLM backends
- DuckDB-based memory system with vector search
- Local file storage support
- Rich-based console logging
- Multi-user support with conversation isolation
- YAML-based configuration system
- Environment variable substitution
- Docker and cloud infrastructure support
- Command-line interface (entity-cli)
- Workflow visualization tool
- Comprehensive test suite with pytest
- GitHub Actions CI/CD pipeline
- MIT License

[Unreleased]: https://github.com/Ladvien/entity/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/Ladvien/entity/releases/tag/v0.0.1