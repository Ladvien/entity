# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses Poetry for dependency management and Poethepoet (poe) for task automation.

### Core Development Commands
- `poetry run entity-cli --config config/dev.yaml` - Run the Entity CLI with development config
- `poetry run entity-cli --config config/dev.yaml verify` - Verify configuration is valid
- `poe test` - Run tests with pytest
- `poe test-verbose` - Run tests with verbose output
- `poe test-coverage` - Run tests with coverage reporting
- `poe lint` - Run code formatting (black, isort) and linting (flake8)
- `poe check` - Full validation pipeline: lint, mypy, bandit, validate configs, pytest
- `poe validate` - Validate configurations and registry

### Documentation
- `poe docs` - Build documentation with Sphinx
- `poe docs_view` - Live documentation server with auto-rebuild

### Testing Markers
Use pytest markers to run specific test categories:
- `pytest -m unit` - Fast unit tests
- `pytest -m integration` - Integration tests with real components
- `pytest -m memory` - Memory system tests
- `pytest -m tools` - Tool system tests
- `pytest -m cli` - CLI interface tests

## Architecture Overview

### Core Components
The Entity Pipeline Framework is built around a 4-layer plugin architecture:

1. **Agent Class** (`src/entity/core/agent.py`) - High-level wrapper combining builder and runtime
2. **Pipeline System** (`src/pipeline/pipeline.py`) - Message execution engine using workflows
3. **Plugin System** - Three-layer progressive complexity:
   - Infrastructure Plugins (Layer 1)
   - Resource Interface Plugins (Layer 2) 
   - Processing Plugins (execution stages)
4. **Resource Management** (`src/entity/core/resources/`) - Dependency injection container

### Key Architectural Patterns
- **Stateless Workers**: Horizontal scaling with persistent state in DuckDB/PostgreSQL
- **Plugin Stages**: `pre_llm`, `llm`, `post_llm`, `tool_execution`, `adapter` execution phases
- **Resource Injection**: Dependencies provided through ResourceContainer
- **Configuration-Driven**: Single YAML file defines entire agent pipeline

### Directory Structure
- `src/entity/` - Main Entity framework package
- `src/pipeline/` - Core pipeline execution engine
- `src/plugins/builtin/` - Built-in plugins (adapters, resources)
- `user_plugins/` - Custom/example plugins for local development
- `examples/` - Complete agent examples (basic, intermediate, advanced)
- `config/` - YAML configurations for dev/prod environments

### Plugin Development
Plugins inherit from base classes in `src/entity/core/plugins/base.py`:
- `PromptPlugin` - LLM interaction logic
- `ToolPlugin` - Tool execution and discovery
- `AdapterPlugin` - Interface adapters (CLI, HTTP, WebSocket)
- `ResourcePlugin` - Resource implementations
- `FailurePlugin` - Error handling

### Configuration Files
- `config/dev.yaml` - Development configuration with in-memory DuckDB
- `config/prod.yaml` - Production configuration
- Hot-reloadable with validation on changes

### Memory System
Unified memory resource handles chat history, vector search, and general storage using DuckDB (local) or PostgreSQL + pgvector (production).

## Development Workflow

1. Make changes to source code
2. Run `poe lint` to format and check code style
3. Run `poe test` to verify functionality
4. Run `poe validate` to check configuration validity
5. Use `poe check` for comprehensive validation before commits

The framework emphasizes configuration over code - most agent behavior is defined in YAML rather than Python code changes.