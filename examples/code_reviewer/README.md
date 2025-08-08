# Code Reviewer Agent - Production-Ready Code Analysis with Entity

## 🎯 Why This Example Matters

**Transform code review from hours to seconds** with Entity's plugin architecture.

This example shows how Entity Framework makes building specialized AI agents (like code reviewers) dramatically simpler and more powerful than traditional approaches.

## 💡 The Problem It Solves

### Without Entity Framework
```python
# 1000+ lines of code needed for:
# - File parsing and traversal
# - Language detection
# - LLM integration
# - Result formatting
# - Error handling
# - Configuration management
# - Testing infrastructure
```

### With Entity Framework
```python
# 100 lines of focused plugin code
# All infrastructure handled by Entity
agent = Agent.from_config("reviewer_config.yaml")
await agent.chat("Review ./src")  # That's it!
```

## 🚀 Real-World Impact

### For Development Teams
- **Instant PR reviews** - Get feedback in seconds
- **Consistent standards** - Same review criteria every time
- **Knowledge capture** - Encode best practices in plugins

### For Solo Developers
- **24/7 code mentor** - Always available for feedback
- **Learn best practices** - Educational explanations
- **Catch bugs early** - Before they reach production

### For Enterprises
- **Standardize reviews** across all teams
- **Compliance checking** built into workflow
- **Audit trail** with Entity's logging

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         reviewer_config.yaml            │
│    (Review Rules & Configuration)       │
└──────────────┬──────────────────────────┘
               │
               ▼
        ╔═══════════════╗
        ║ INPUT STAGE   ║
        ╟───────────────╢
        ║ CodeInputPlugin║ → Handles files, dirs, diffs
        ╚═══════╤═══════╝
               │
        ╔═══════════════╗
        ║ PARSE STAGE   ║
        ╟───────────────╢
        ║ CodeParser    ║ → Language detection, AST
        ╚═══════╤═══════╝
               │
        ╔═══════════════╗
        ║ THINK STAGE   ║
        ╟───────────────╢
        ║ ReviewAnalyzer║ → Apply review rules
        ╚═══════╤═══════╝
               │
        ╔═══════════════╗
        ║ DO STAGE      ║
        ╟───────────────╢
        ║ SecurityCheck ║ → Scan for vulnerabilities
        ║ PerfAnalyzer  ║ → Performance issues
        ║ StyleChecker  ║ → Code style violations
        ╚═══════╤═══════╝
               │
        ╔═══════════════╗
        ║ REVIEW STAGE  ║
        ╟───────────────╢
        ║ PriorityFilter║ → Sort by severity
        ╚═══════╤═══════╝
               │
        ╔═══════════════╗
        ║ OUTPUT STAGE  ║
        ╟───────────────╢
        ║ ReportFormatter║ → Markdown/JSON/HTML
        ╚═══════════════╝
```

## 📦 Plugin Showcase

### CodeInputPlugin (`plugins/input_plugins.py`)
**Superpower**: Handles any code input format
- 📄 Single files: `review main.py`
- 📁 Directories: `review ./src`
- 📋 Direct code: Paste and review
- 🔀 Git diffs: Review changes
- 🔗 URLs: Review GitHub files

### CodeAnalyzerPlugin (THINK Stage)
**Superpower**: Deep code understanding
- 🧠 AST analysis for structure
- 🔍 Pattern detection
- 🐛 Bug prediction
- 🏗️ Architecture assessment

### SecurityScannerPlugin (DO Stage)
**Superpower**: Vulnerability detection
- 🔐 SQL injection risks
- 🛡️ XSS vulnerabilities
- 🔑 Hardcoded secrets
- 📦 Dependency issues

### ReviewFormatterPlugin (OUTPUT Stage)
**Superpower**: Multiple output formats
- 📝 Markdown reports
- 📊 JSON for CI/CD
- 🌐 HTML for sharing
- 💬 Inline comments

## 🎮 Usage Examples

### Basic File Review
```bash
python code_reviewer.py
> review main.py
```

### Directory Analysis
```bash
python code_reviewer.py
> analyze ./src --recursive
```

### Git Diff Review
```bash
git diff | python code_reviewer.py
```

### CI/CD Integration
```yaml
# .github/workflows/review.yml
- name: Code Review
  run: |
    pip install entity-core
    python code_reviewer.py --path ${{ github.workspace }} --output json
```

## 🔧 Customization

### Add Language-Specific Rules
```yaml
# reviewer_config.yaml
think:
  - code_reviewer.plugins.PythonAnalyzer:
      check_type_hints: true
      enforce_pep8: true

  - code_reviewer.plugins.JavaScriptAnalyzer:
      prefer_const: true
      check_async_await: true
```

### Add Custom Security Checks
```yaml
do:
  - code_reviewer.plugins.CustomSecurityPlugin:
      check_api_keys: true
      scan_patterns:
        - "password.*=.*['\"]"
        - "api_key.*=.*['\"]"
```

### Integrate with Your Tools
```yaml
output:
  - code_reviewer.plugins.JiraIntegration:
      project_key: "DEV"
      create_tickets: true

  - code_reviewer.plugins.SlackNotifier:
      webhook_url: ${SLACK_WEBHOOK}
      severity_threshold: "high"
```

## 📊 Performance Comparison

| Feature | Traditional Tool | Entity Code Reviewer |
|---------|-----------------|---------------------|
| Setup Time | 2-3 hours | 5 minutes |
| Lines of Code | 1500+ | 150 |
| Extensibility | Hard-coded | Plugin-based |
| Language Support | Limited | Unlimited via plugins |
| Custom Rules | Regex only | Full programmatic |
| Output Formats | 1-2 | Unlimited |
| Testing | Complex | Simple unit tests |
| Maintenance | High effort | Low effort |

## 🧪 Testing Your Plugins

```python
# test_code_input_plugin.py
import pytest
from code_reviewer.plugins.input_plugins import CodeInputPlugin

@pytest.mark.asyncio
async def test_file_detection():
    plugin = CodeInputPlugin(resources={}, config={})
    context = MockContext()
    context.message = "review ./main.py"

    await plugin.execute(context)

    assert context.memory["input_type"] == "file"
    assert context.memory["file_path"] == "./main.py"
```

## 🎯 Real Use Cases

### 1. Pre-Commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python code_reviewer.py --staged-files --fail-on-critical
```

### 2. PR Bot
```python
# GitHub Action or CI/CD
async def review_pr(pr_number):
    diff = await github.get_pr_diff(pr_number)
    agent = Agent.from_config("reviewer_config.yaml")
    review = await agent.chat(f"review diff:\n{diff}")
    await github.post_comment(pr_number, review)
```

### 3. Learning Tool
```yaml
# educational_config.yaml
think:
  - code_reviewer.plugins.EducationalAnalyzer:
      explain_issues: true
      suggest_improvements: true
      provide_examples: true
```

## 🚀 Advanced Features

### Incremental Reviews
```yaml
input:
  - code_reviewer.plugins.IncrementalInputPlugin:
      cache_previous: true
      diff_only: true
```

### Multi-Language Support
```yaml
parse:
  - code_reviewer.plugins.PolyglotParser:
      languages: ["python", "javascript", "go", "rust"]
      unified_ast: true
```

### AI-Powered Suggestions
```yaml
do:
  - code_reviewer.plugins.RefactoringSuggester:
      suggest_improvements: true
      generate_patches: true
```

## 📈 Metrics & Monitoring

Entity automatically tracks:
- Review completion time
- Issues found per category
- Plugin execution performance
- Resource utilization

Access via Entity's logging:
```python
logger = context.get_resource("logging")
metrics = await logger.get_metrics("code_review_session")
```

## 🎓 Learning Path

1. **Start Here**: Run basic file review
2. **Customize**: Modify severity thresholds
3. **Extend**: Add a custom check plugin
4. **Integrate**: Connect to your CI/CD
5. **Share**: Publish your plugins

## 🤝 Contributing

Share your code review plugins:
1. Follow Entity plugin patterns
2. Include comprehensive tests
3. Document configuration options
4. Provide usage examples
5. Submit PR with benchmarks

## 🔗 Related Examples

- **`simple_chat/`** - Basic plugin structure
- **`research_assistant/`** - Complex multi-stage workflow
- **`security_analyzer/`** - Specialized analysis plugins

---

**Entity Framework**: *Turn every developer into a 10x engineer.* 🚀
