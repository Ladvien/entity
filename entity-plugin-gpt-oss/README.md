# Entity Plugin: GPT-OSS Integration

[![Tests](https://github.com/Ladvien/entity-plugin-gpt-oss/actions/workflows/test.yml/badge.svg)](https://github.com/Ladvien/entity-plugin-gpt-oss/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/Ladvien/entity-plugin-gpt-oss/branch/main/graph/badge.svg)](https://codecov.io/gh/Ladvien/entity-plugin-gpt-oss)
[![PyPI version](https://badge.fury.io/py/entity-plugin-gpt-oss.svg)](https://badge.fury.io/py/entity-plugin-gpt-oss)
[![Python versions](https://img.shields.io/pypi/pyversions/entity-plugin-gpt-oss.svg)](https://pypi.org/project/entity-plugin-gpt-oss/)
[![License](https://img.shields.io/github/license/Ladvien/entity-plugin-gpt-oss.svg)](https://github.com/Ladvien/entity-plugin-gpt-oss/blob/main/LICENSE)

## 📋 Description

A comprehensive suite of GPT-OSS integration plugins for the Entity Framework. This plugin collection enables seamless integration with GPT-OSS (OpenAI's GPT with Tools) capabilities, providing advanced reasoning, tool orchestration, safety filtering, and analytics functionality.

## ✨ Features

### Core Plugins
- **ReasoningTracePlugin** - Captures and analyzes chain-of-thought reasoning
- **StructuredOutputPlugin** - Ensures consistent JSON/XML output formatting
- **AdaptiveReasoningPlugin** - Dynamic reasoning complexity adjustment
- **GPTOSSToolOrchestrator** - Native browser and Python tool integration

### Advanced Features
- **DeveloperOverridePlugin** - Manual intervention and debugging capabilities
- **MultiChannelAggregatorPlugin** - Combines multiple GPT-OSS response channels
- **HarmonySafetyFilterPlugin** - Content safety and compliance filtering
- **FunctionSchemaRegistryPlugin** - Dynamic function schema management
- **ReasoningAnalyticsDashboardPlugin** - Performance and reasoning analytics

## 📦 Installation

### From PyPI

```bash
pip install entity-plugin-gpt-oss
```

### From Source

```bash
git clone https://github.com/Ladvien/entity-plugin-gpt-oss.git
cd entity-plugin-gpt-oss
pip install -e .
```

### As Entity Framework Submodule

```bash
# From entity-core root directory
git submodule add https://github.com/Ladvien/entity-plugin-gpt-oss.git plugins/gpt-oss
git submodule update --init --recursive
```

## 🚀 Usage

### Basic Integration

```python
from entity_plugin_gpt_oss import (
    ReasoningTracePlugin,
    GPTOSSToolOrchestrator,
    StructuredOutputPlugin
)
from entity.workflow.executor import WorkflowExecutor

# Initialize plugins
reasoning_trace = ReasoningTracePlugin(config={
    "capture_level": "detailed",
    "storage_backend": "memory"
})

tool_orchestrator = GPTOSSToolOrchestrator(config={
    "enabled_tools": ["browser", "python"],
    "sandbox_mode": true,
    "rate_limits": {
        "browser": "10/minute",
        "python": "5/minute"
    }
})

structured_output = StructuredOutputPlugin(config={
    "enforce_schema": true,
    "output_format": "json"
})

# Add to workflow
executor = WorkflowExecutor()
executor.add_plugin(reasoning_trace, stage="processing")
executor.add_plugin(tool_orchestrator, stage="processing")
executor.add_plugin(structured_output, stage="postprocessing")

# Execute workflow with GPT-OSS capabilities
result = await executor.run({
    "prompt": "Research the latest developments in AI safety",
    "tools_required": ["browser", "python"],
    "output_format": "detailed_report"
})
```

### Advanced Configuration

```python
from entity_plugin_gpt_oss import (
    AdaptiveReasoningPlugin,
    HarmonySafetyFilterPlugin,
    ReasoningAnalyticsDashboardPlugin
)

# Adaptive reasoning based on task complexity
adaptive_reasoning = AdaptiveReasoningPlugin(config={
    "complexity_thresholds": {
        "simple": 0.3,
        "moderate": 0.6,
        "complex": 0.9
    },
    "reasoning_models": {
        "simple": "gpt-3.5-turbo",
        "moderate": "gpt-4",
        "complex": "gpt-4-32k"
    }
})

# Safety filtering with custom rules
safety_filter = HarmonySafetyFilterPlugin(config={
    "filter_level": "moderate",
    "custom_rules": [
        "no_personal_data_extraction",
        "no_harmful_content_generation"
    ],
    "whitelist_domains": ["wikipedia.org", "arxiv.org"]
})

# Analytics and monitoring
analytics = ReasoningAnalyticsDashboardPlugin(config={
    "metrics_collection": true,
    "dashboard_port": 8080,
    "export_formats": ["json", "csv", "prometheus"]
})
```

### Configuration via YAML

```yaml
# config.yaml
plugins:
  - name: ReasoningTracePlugin
    stage: processing
    config:
      capture_level: detailed
      trace_storage: persistent
      analysis_depth: deep

  - name: GPTOSSToolOrchestrator
    stage: processing
    config:
      enabled_tools:
        - browser
        - python
      security:
        sandbox_mode: true
        network_isolation: true
      rate_limits:
        browser: "10/minute"
        python: "5/minute"

  - name: HarmonySafetyFilterPlugin
    stage: preprocessing
    config:
      filter_level: strict
      compliance_standards: ["GDPR", "CCPA"]
      content_categories:
        block: ["harmful", "offensive", "personal_data"]
        warn: ["sensitive", "commercial"]
```

## 🔧 Development Setup

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- Entity Framework Core
- GPT-OSS API access

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Ladvien/entity-plugin-gpt-oss.git
cd entity-plugin-gpt-oss
```

2. Install dependencies:
```bash
poetry install
```

3. Run tests:
```bash
poetry run pytest
```

4. Run linting and type checking:
```bash
poetry run ruff check .
poetry run black --check .
poetry run mypy src
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific plugin tests
poetry run pytest tests/test_reasoning_trace.py

# Run integration tests
poetry run pytest tests/integration/

# Run with verbose output
poetry run pytest -v
```

## 📝 API Reference

### ReasoningTracePlugin

Captures and analyzes GPT-OSS chain-of-thought reasoning for debugging and improvement.

**Configuration:**
- `capture_level` (str): Level of detail to capture ("basic", "detailed", "comprehensive")
- `storage_backend` (str): Storage backend for traces ("memory", "file", "database")
- `analysis_depth` (str): Depth of reasoning analysis ("shallow", "deep")
- `trace_retention_days` (int): How long to retain traces

**Methods:**
- `extract_reasoning(response)`: Extract reasoning chains from GPT-OSS responses
- `analyze_patterns()`: Analyze reasoning patterns for optimization
- `export_traces(format)`: Export captured traces in various formats

### GPTOSSToolOrchestrator

Orchestrates GPT-OSS native browser and Python tools within Entity workflows.

**Configuration:**
- `enabled_tools` (list): List of enabled tools ("browser", "python", "bash")
- `sandbox_mode` (bool): Enable sandboxed execution
- `rate_limits` (dict): Rate limits per tool type
- `security_settings` (dict): Security configuration

**Methods:**
- `execute_tool(tool_type, command)`: Execute tool commands safely
- `get_tool_status()`: Check status of all tools
- `configure_security()`: Update security settings dynamically

### StructuredOutputPlugin

Ensures GPT-OSS responses conform to specified structured formats.

**Configuration:**
- `output_format` (str): Target format ("json", "xml", "yaml")
- `enforce_schema` (bool): Strictly enforce schema validation
- `schema_definitions` (dict): Custom schema definitions
- `fallback_behavior` (str): Behavior when validation fails

### HarmonySafetyFilterPlugin

Advanced safety filtering for GPT-OSS responses with compliance features.

**Configuration:**
- `filter_level` (str): Filtering intensity ("permissive", "moderate", "strict")
- `compliance_standards` (list): Standards to comply with ("GDPR", "CCPA", "HIPAA")
- `custom_rules` (list): Custom filtering rules
- `audit_logging` (bool): Enable audit trail logging

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-gpt-oss-feature`)
3. Commit your changes (`git commit -m 'Add amazing GPT-OSS feature'`)
4. Push to the branch (`git push origin feature/amazing-gpt-oss-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add comprehensive tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR
- Keep commits atomic and well-described
- Add type hints for all new code

### Plugin Development

When adding new GPT-OSS plugins:
1. Inherit from appropriate base classes
2. Implement required abstract methods
3. Add comprehensive test coverage (>90%)
4. Include usage examples in docstrings
5. Update API documentation

## 🔒 Security Considerations

- All tool executions run in sandboxed environments
- Network access is controlled and monitored
- Content filtering prevents harmful outputs
- Audit logging tracks all plugin activities
- Rate limiting prevents resource abuse
- Input validation prevents injection attacks

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Entity Framework Core](https://github.com/Ladvien/entity)
- [GPT-OSS Documentation](https://gpt-oss.readthedocs.io)
- [PyPI Package](https://pypi.org/project/entity-plugin-gpt-oss/)
- [Issue Tracker](https://github.com/Ladvien/entity-plugin-gpt-oss/issues)

## 🏷️ Version History

- **0.1.0** - Initial release
  - Core GPT-OSS integration plugins
  - Tool orchestration capabilities
  - Safety filtering and compliance
  - Analytics and monitoring features

## 🙏 Acknowledgments

- Entity Framework team
- OpenAI GPT-OSS team
- Contributors and community members

---

**Note:** This plugin suite is part of the Entity Framework ecosystem. For more information about Entity Framework, visit the [main repository](https://github.com/Ladvien/entity).
